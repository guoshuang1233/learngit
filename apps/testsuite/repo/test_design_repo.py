from common.base_repo import BaseRepo
from apps.testsuite.models import BusinessModule, TestDesignJob, TestSuite
from apps.testcase.models import TestCase


class _UpdateRecordMixin:
    @classmethod
    def update_record(cls, record, **fields):
        for key, value in fields.items():
            setattr(record, key, value)
        record.save(update_fields=list(fields.keys()))
        return record


class BusinessModuleRepo(_UpdateRecordMixin, BaseRepo):
    model = BusinessModule


class TestDesignJobRepo(_UpdateRecordMixin, BaseRepo):
    model = TestDesignJob


class TestSuiteRepo(_UpdateRecordMixin, BaseRepo):
    model = TestSuite


class TestCaseAssetRepo(_UpdateRecordMixin, BaseRepo):
    model = TestCase
