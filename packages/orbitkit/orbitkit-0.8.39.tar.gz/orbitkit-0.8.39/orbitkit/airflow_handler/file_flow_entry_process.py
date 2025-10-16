import os
from collections import Counter
from datetime import datetime
from typing import Literal
import logging
import pymongo
import pytz
import boto3
from sqlalchemy import create_engine, Table, MetaData, select
from sqlalchemy.orm import sessionmaker, scoped_session
from contextlib import contextmanager

from orbitkit.airflow_handler.file_handler_v2 import FileFlowHandleV2
from orbitkit.airflow_handler.data_preprocessing import DocumentProcessor
from orbitkit.orbit_type import OrbitTypeMatcher

logger = logging.getLogger(__name__)


class FilingOfficialProcessor:

    def __init__(self, mongo_uri=None, postgres_uri=None, aws_access_key_id=None, aws_secret_access_key=None, pi2_postgres_uri=None, pi2_database_name=None):
        mongo_uri = os.environ.get('MONGO_URI_MAIN_USER_APP') if not mongo_uri else mongo_uri
        if not mongo_uri:
            raise KeyError('mongo_uri not set.')

        if not aws_secret_access_key or not aws_access_key_id:
            raise KeyError('aws_access_key_id and aws_secret_access_key not set.')

        self.mongo_client = pymongo.MongoClient(mongo_uri)
        self.data_xbrl_convert_collection = self.mongo_client['filing_reports']['data_xbrl_convert']
        self.filing_data_collection = self.mongo_client['filing_reports']['filing_data']
        self.filing_reports_astock_test0822_collection = self.mongo_client['filing_reports']['filing_reports_astock_test0822']
        self.annotation_reports_view_rows_collection = self.mongo_client['filing_reports'][
            'annotation_reports_view_rows']
        self.source_map = {
            'filing_data': (self.filing_data_collection, 'filing_data'),
            'filing_reports_astock_test0822': (self.filing_reports_astock_test0822_collection, 'filing_reports_astock_test0822'),
            'reports_view': [
                (self.filing_data_collection, 'filing_data'),
                (self.filing_reports_astock_test0822_collection, 'filing_reports_astock_test0822')
            ]
        }
        self.only_low_important_set = {'internal_seekingalpha'}
        postgres_uri = os.environ.get('PG_URI_AIRFLOW12_USER_NEWSFEEDSITE') if not postgres_uri else postgres_uri
        if not postgres_uri:
            raise KeyError('postgres_uri not set.')
        self.file_handler = FileFlowHandleV2(postgres_uri=postgres_uri)
        self.data_processor = DocumentProcessor()
        self.max_batch_size = 10000
        self.all_stat_count = {'all': 0, 'skip': 0, 'step_error': 0, 'xbrl': 0, 'file_flow': 0}

        self.s3_client = boto3.client('s3', aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key)
        self.matcher = OrbitTypeMatcher(self.s3_client)
        self.report_type_id_name_map = {i["lv3_id"]: i["lv3_name"] for i in self.matcher.get_full_type_list()}

        self.pi2_postgres_uri = pi2_postgres_uri or os.environ['PG_URI_CX45_USER_GLAUUIADMIN']
        if not self.pi2_postgres_uri:
            raise KeyError('pie_postgres_uri not set.')
        self.databases = pi2_database_name or 'newsfeedsite'
        self.postgres_engine = create_engine(f"{self.pi2_postgres_uri}/{self.databases}", connect_args={"sslmode": "require"})
        self.postgres_session = sessionmaker(bind=self.postgres_engine)
        self.Session = scoped_session(self.postgres_session)
        self.postgres_metadata = MetaData()

        self.pi2_table = Table(
            'primary_instrument_2_release', self.postgres_metadata,
            autoload_with=self.postgres_engine, schema='security_master'
        )

    @contextmanager
    def session_scope(self):
        session = self.Session()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            self.Session.remove()

    def create_spider_name_source_type_map(self, collections):

        def find_duplicates(keys):
            return [k for k, v in Counter(keys).items() if v > 1]

        map_dict = {}
        pipeline = [{'$group': {'_id': "$x_spider_name"}}]

        for collection, label in collections:
            for document in collection.aggregate(pipeline):
                map_dict[document['_id']] = label

        all_keys = list(map_dict.keys())
        duplicates = find_duplicates(all_keys)
        if duplicates:
            raise KeyError(f"Duplicate x_spider_name found: {duplicates}")

        return map_dict

    def send_xbrl_data_to_mongo(self, xbrl_data_list):
        if not xbrl_data_list:
            return
        report_id_list = list(set([i['_id'] for i in xbrl_data_list]))
        result = self.data_xbrl_convert_collection.find({'_id': {'$in': report_id_list}}, {'_id': 1}).batch_size(self.max_batch_size)
        exists_id_list = [i['_id'] for i in result]
        new_xbrl_data_list = [i for i in xbrl_data_list if i['_id'] not in exists_id_list]
        if not new_xbrl_data_list:
            return
        self.data_xbrl_convert_collection.insert_many(new_xbrl_data_list)
        logger.info(f'{len(new_xbrl_data_list)}-xbrl data inserted.')

    def update_doc_status_to_convert(self, collection, report_id_list):
        if len(report_id_list) == 0:
            return
        collection.update_many({
            '_id': {'$in': report_id_list}
        }, {'$set': {
            "x_status_list.status_convert.status": "convert_failed",
            "x_status_list.status_convert.status_txt": "convert_txt_init",
            "x_status_list.status_convert.status_meta": "meta_init",
            "x_updated_date": datetime.now(tz=pytz.timezone('UTC')).strftime("%Y-%m-%dT%H:%M:%S%z"),
        }})
        logger.info(f'The document file type cannot be converted.')

    def update_extends_fields(self, perm_id_list, file_flow_info):
        stmt = select(self.pi2_table.c.orbit_entity_id, self.pi2_table.c.ticker).where(self.pi2_table.c.orbit_entity_id.in_(perm_id_list))
        orbit_entity_id_ticker_map = {}
        with self.session_scope() as session:
            result = session.execute(stmt)
            for row in result:
                if row.orbit_entity_id not in orbit_entity_id_ticker_map:
                    orbit_entity_id_ticker_map[row.orbit_entity_id] = []

                if row.ticker is not None:
                    orbit_entity_id_ticker_map[row.orbit_entity_id].append(row.ticker)
        for step_info, records in file_flow_info.items():
            for record in records:
                if 'extends' in record and record.get('extends') is not None:
                    tickers = []
                    for i in record['extends']['perm_id_list']:
                        tickers.extend(orbit_entity_id_ticker_map.get(i, []))
                    record['extends']['tickers'] = tickers

                    record['extends']['report_type_id_list_str'] = [self.report_type_id_name_map.get(i) for i in record['extends']['report_type_id_list_str']]

        return file_flow_info

    def send_task(self, file_flow_info, tags, is_important, priority, spider_name_source_type):
        for step_str, records in file_flow_info.items():
            steps = step_str.split('@__@')
            start_stage = steps[0]
            target_stage = steps[1]
            x_spider_name = steps[2]

            if start_stage == 'success' or target_stage == 'success':
                self.all_stat_count['skip'] += len(records)
                logger.info(
                    f"{len(records)}--{start_stage}-{target_stage}-{x_spider_name} status: False, message: 'File has already completed the embedding stage.' ")
                continue

            if is_important and x_spider_name not in self.only_low_important_set:
                logger.info(f"is_important: {is_important} - {x_spider_name}")
                status, ids, message = self.file_handler.entry_point_urgent(records=records, start_stage=start_stage,
                                                                            target_stage=target_stage,
                                                                            tags=tags,
                                                                            tag=x_spider_name,
                                                                            priority=priority,
                                                                            source_type=spider_name_source_type[
                                                                                x_spider_name])
            else:
                status, ids, message = self.file_handler.entry_point(records=records, start_stage=start_stage,
                                                                     target_stage=target_stage, tags=tags,tag=x_spider_name,
                                                                     priority=priority,
                                                                     source_type=spider_name_source_type[x_spider_name])
            self.all_stat_count['file_flow'] += len(records)
            logger.info(f"{len(records)}--{start_stage}-{target_stage}-{x_spider_name} status: {status}, message: {message}")


    def process_task_entry(self, source: Literal["filing_data", "filing_reports_astock_test0822", "reports_view"],
                           query: dict, tags: list[str], priority: str,
                           is_important: bool = False, check_doc: bool = True):

        if source == 'reports_view':
            collections = self.source_map[source]
        else:
            collections = [self.source_map[source]]

        spider_name_source_type = self.create_spider_name_source_type_map(collections)

        process_data = []
        perm_id_set = set()
        for collection, label in collections:
            logger.info(f"load {label} data.")
            docs = collection.find(query).batch_size(1000)

            for doc in docs:
                self.all_stat_count['all'] += 1
                for orbit_entity_id in doc['x_orbit_data']['perm_id_list']:
                    perm_id_set.add(orbit_entity_id)
                process_data.append(self.data_processor.process(doc, check_doc))
                if len(process_data) >= self.max_batch_size:
                    file_flow_info, xbrl_data, except_id_list, doc_error_list = self.data_processor.split_data_by_spider_name_and_step(
                        process_data)
                    file_flow_info = self.update_extends_fields(list(perm_id_set), file_flow_info)
                    self.all_stat_count['skip'] += len(doc_error_list)
                    self.all_stat_count['step_error'] += len(except_id_list)
                    self.all_stat_count['xbrl'] += len(xbrl_data)
                    self.send_task(file_flow_info, tags, is_important, priority, spider_name_source_type)
                    self.send_xbrl_data_to_mongo(xbrl_data)
                    self.update_doc_status_to_convert(collection, doc_error_list)
                    process_data.clear()
                    perm_id_set.clear()

            if process_data:
                file_flow_info, xbrl_data, except_id_list, doc_error_list = self.data_processor.split_data_by_spider_name_and_step(
                    process_data)
                file_flow_info = self.update_extends_fields(list(perm_id_set), file_flow_info)
                self.all_stat_count['skip'] += len(doc_error_list)
                self.all_stat_count['step_error'] += len(except_id_list)
                self.all_stat_count['xbrl'] += len(xbrl_data)
                self.send_task(file_flow_info, tags, is_important, priority, spider_name_source_type)
                self.send_xbrl_data_to_mongo(xbrl_data)
                self.update_doc_status_to_convert(collection, doc_error_list)
                process_data.clear()
                perm_id_set.clear()

        logger.info(f"finish processing {self.all_stat_count}.")
