from functools import cached_property
from typing import List

import mfire.utils.mfxarray as xr
from mfire.composite.base import BaseComposite, precached_property
from tests.composite.factories import BaseCompositeFactory


class TestBaseComposite:
    basic_data = xr.DataArray([1, 2, 3])

    def test_make_copy(self):
        # Test of deep=True argument in make_copy
        class BaseCompositeTest(BaseCompositeFactory):
            a: list = [1, 2]

        obj1 = BaseCompositeTest()
        obj2 = obj1.make_copy()
        obj1.a.append(3)
        assert obj2.a == [1, 2]

    def test_handle_children(self):
        # Test when the shared config is given to children
        class BaseCompositeTest(BaseComposite):
            _shared_config: dict = {}
            obj: BaseComposite = BaseComposite()
            objs: List[BaseComposite] = [BaseComposite(), BaseComposite()]

        composite = BaseCompositeTest()
        composite.shared_config["a"] = "b"
        assert composite.obj.parent is not None
        assert composite.obj.shared_config == {"a": "b"}
        assert composite.objs[0].shared_config == {"a": "b"}
        assert composite.objs[1].shared_config == {"a": "b"}
        assert composite.objs[0] is not None
        assert composite.objs[1] is not None

        # Test when the parent is already defined
        class BaseCompositeTestChild(BaseComposite):
            parent: BaseComposite = BaseCompositeFactory(
                shared_config_factory={"a": "b"}
            )

        class BaseCompositeTestBis(BaseComposite):
            shared_config: dict = {"c": "d"}
            obj: BaseCompositeTestChild = BaseCompositeTestChild()

        assert BaseCompositeTestBis().obj.parent.shared_config == {"a": "b"}

    def test_time_zone(self):
        composite = BaseCompositeFactory(shared_config_factory={"time_zone": "XXX"})
        assert composite.time_zone == "XXX"

    def test_language(self):
        composite = BaseCompositeFactory(shared_config_factory={"language": "XXX"})
        assert composite.language == "XXX"

    def test_set_language(self):
        composite = BaseCompositeFactory(
            shared_config_factory={"language": "XXX", "translation": ...}
        )
        composite.set_language("YYY")
        assert composite.language == "YYY"
        assert "translation" not in composite.shared_config

    def test_translation(self):
        composite = BaseCompositeFactory()

        assert {
            language: composite._("en dessous de")
            for language in composite.iter_languages()
        } == {"fr": "en dessous de", "en": "under", "es": "por debajo"}

    def test_reset(self):
        # Test of translation and children reset
        class TestBaseCompositeFactoryChild(BaseCompositeFactory):
            a: int = 1

            def reset(self):
                super().reset()
                self.a = 2

        class TestBaseCompositeFactoryParent(TestBaseCompositeFactoryChild):
            child: TestBaseCompositeFactoryChild = TestBaseCompositeFactoryChild()
            children: List[TestBaseCompositeFactoryChild] = [
                TestBaseCompositeFactoryChild(),
                TestBaseCompositeFactoryChild(),
            ]

        composite = TestBaseCompositeFactoryParent(
            shared_config_factory={"translation": ...}
        )
        composite.reset()

        assert composite.a == 2
        assert composite.child.a == 2
        assert composite.children[0].a == 2
        assert composite.children[1].a == 2

        # Test of reset of cached and precached properties
        class TestBaseCompositeFactory(BaseCompositeFactory):
            a: int = 0
            b: int = 0

            @cached_property
            def f1(self):
                self.a += 1
                return self.a

            @precached_property
            def f2(self):
                self.b += 1
                return self.b

        composite = TestBaseCompositeFactory()
        assert composite.f1 == 1
        assert composite.f1 == 1
        assert composite.f2 == 1
        assert composite.f2 == 1

        composite.reset()
        assert composite.f1 == 2
        assert composite.f2 == 2

    def test_compute(self, tmp_path_cwd):
        assert BaseCompositeFactory().compute() is None
