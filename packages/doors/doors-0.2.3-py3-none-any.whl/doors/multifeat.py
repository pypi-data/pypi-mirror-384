import logging
import time
from multiprocessing import JoinableQueue, Manager, Process

import numpy as np
import pandas as pd

import doors as wu

FEATURE_PREFIX = "feat:"


def generate_features(df, features, helpers, n_jobs=4):
    helpers = [] if helpers is None else helpers
    if n_jobs == 1:
        manager = SerialFeatureGenerator()
    else:
        manager = ParallelFeatureGenerator(n_jobs)
    feat_df = manager.generate_features(df, features, helpers)
    return feat_df


class _FeatureGenerator(object):
    feature_prefix = FEATURE_PREFIX

    def namer(self, func):
        return wu.strings.as_string(func)

    def generate_features(self, df, features, helpers):
        df = df.copy(deep=False)
        helper_df = self._generate_helpers(df, helpers)
        df = pd.concat([df, helper_df], axis=1)
        feat_df = self._generate_features(df, features)
        feat_df = pd.concat([feat_df, helper_df], axis=1)
        return feat_df

    def _log_func(self, func):
        logger = logging.getLogger(__name__)

        def wrapped_func(*args, **kwargs):
            start = time.time()
            logger.debug("Adding {}")
            name = wu.strings.as_string(func)
            results = func(*args, **kwargs)
            end = time.time()
            elapsed = end - start
            logger.debug("Added {}: (time {})".format(name, elapsed))
            return results

        return wrapped_func

    def _postprocess_features(self, values):
        return values.astype("float32")

    def _generate_helpers(self, df, helpers):
        helper_df = pd.DataFrame()
        logger = logging.getLogger(__name__)
        for func in helpers:
            func_name = self.namer(func)
            logger.debug("Adding helper: " + func_name)
            result = func(df)
            helpers = self._sanitise(result)
            for values, name in helpers:
                name = func_name if name is None else name
                helper_df[name] = values
        return helper_df

    def _sanitise(self, result):
        if isinstance(result, np.ndarray):
            values = result
            name = None
            results = [(values, name)]
        elif isinstance(result, tuple):
            values, name = result
            if isinstance(name, list):
                results = zip(values, name)
            else:
                results = [result]
        elif isinstance(result, list):
            results = result
        return results

    def __repr__(self):
        return type(self).__name__


class SeriallyAddFeaturesMixin(object):
    def _generate_features(self, df, features):
        feat_df = pd.DataFrame()
        logger = logging.getLogger(__name__)
        for func in features:
            func_name = self.namer(func)
            logger.debug("Adding features: " + func_name)
            result = func(df)
            sanitised_results = self._sanitise(result)
            # if func_name == 'partial(func=raw_column, column=years_to_foaling_date)':
            #     import pdb;pdb.set_trace()
            for value, name in sanitised_results:
                name = func_name if name is None else name
                feat_name = "feat:" + name
                value = self._postprocess_features(value)
                df[feat_name] = value
                feat_df[feat_name] = value
        return feat_df


class ParallelAddFeaturesMixin(object):
    def __init__(self, n_jobs):
        self.n_jobs = n_jobs
        self._queue = JoinableQueue()
        self._logger = logging.getLogger(__name__)

    def _generate_features(self, df, features):
        map(self._queue.put, features)
        self._set_processes(df)
        self._start_processes()
        self._terminate()
        feat_df = pd.DataFrame(self.return_dict)
        return feat_df

    def _set_processes(self, df):
        manager = Manager()
        self.return_dict = manager.dict()
        self.processes = []
        for i in range(self.n_jobs):
            proc = Process(target=self._get_feature, args=(df, self.return_dict, i))
            self.processes.append(proc)

    def _start_processes(self):
        for p in self.processes:
            p.start()

    def _get_feature(self, df, return_dict, thread_id):
        while True:
            feat = self._queue.get()
            if not feat:
                self._queue.task_done()
                break
            try:
                self._logger.debug(
                    "[thread {}] feature: {}".format(thread_id, self.namer(feat))
                )
                feature = self._get_feat_as_dict(df, feat)
                return_dict.update(feature)
            except KeyError as e:
                self._handle_missing_key(feat, return_dict, df, e)
            self._queue.task_done()

    def _handle_missing_key(self, feat, return_dict, df, exception):
        missing_key = exception.args[0]
        self._logger.debug("Missing key: {}; placing back in queue".format(missing_key))
        if missing_key in return_dict:
            df[missing_key] = return_dict[missing_key]
        self._queue.put(feat)

    def _terminate(self):
        """wait until queue is empty and terminate processes"""
        self._queue.join()
        for p in self.processes:
            p.terminate()

    def _add_features_to_df(self, df, feat_dict):
        for key, values in feat_dict.items():
            df[key] = values
        return df

    def _get_feat_as_dict(self, df, feat):
        result = feat(df)
        sanitised = self._sanitise(result)
        features = {}
        func_name = self.namer(feat)
        for values, name in sanitised:
            name = func_name if name is None else name
            features["feat:" + name] = self._postprocess_features(values)
        return features


class SerialFeatureGenerator(_FeatureGenerator, SeriallyAddFeaturesMixin):
    pass


class ParallelFeatureGenerator(_FeatureGenerator, ParallelAddFeaturesMixin):
    pass
