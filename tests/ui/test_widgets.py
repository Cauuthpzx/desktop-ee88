"""
UI tests cho shared widgets — dùng QTest.
Yêu cầu: QApplication instance (qapp fixture).
"""
import pytest


@pytest.fixture(autouse=True)
def _ensure_qapp(qapp):
    """Mọi test trong file này cần QApplication."""
    pass


@pytest.fixture(autouse=True)
def _init_i18n():
    from core.i18n import init
    init()


@pytest.mark.ui
class TestExpandCard:
    def test_create_without_crash(self):
        from widgets.expand_card import ExpandCard
        card = ExpandCard(title="Test Card")
        assert card is not None
        assert card.is_expanded() is False

    def test_expand_and_collapse(self):
        from widgets.expand_card import ExpandCard
        card = ExpandCard(title="Test")
        card.expand()
        assert card.is_expanded() is True
        card.collapse()
        # Animation may be async, but state should change
        assert card.is_expanded() is False

    def test_toggle(self):
        from widgets.expand_card import ExpandCard
        card = ExpandCard(title="Test")
        card.toggle()
        assert card.is_expanded() is True
        card.toggle()
        assert card.is_expanded() is False

    def test_set_title(self):
        from widgets.expand_card import ExpandCard
        card = ExpandCard(title="Original")
        card.set_title("Updated")
        assert card._title_lbl.text() == "Updated"

    def test_set_description(self):
        from widgets.expand_card import ExpandCard
        card = ExpandCard()
        card.set_description("Some description")
        assert card._desc_lbl.text() == "Some description"


@pytest.mark.ui
class TestEmptyState:
    def test_create_with_defaults(self):
        from widgets.empty_state import EmptyState
        empty = EmptyState()
        assert empty is not None

    def test_create_with_custom_text(self):
        from widgets.empty_state import EmptyState
        empty = EmptyState(title="No Data", description="Add something")
        assert empty._title_lbl.text() == "No Data"
        assert empty._desc_lbl.text() == "Add something"


@pytest.mark.ui
class TestBadge:
    def test_create_badge(self):
        from widgets.badge import Badge
        badge = Badge("Active")
        assert badge is not None

    def test_status_badge(self):
        from widgets.badge import StatusBadge
        badge = StatusBadge("online")
        assert badge is not None


@pytest.mark.ui
class TestSearchBar:
    def test_create(self):
        from widgets.search_bar import SearchBar
        bar = SearchBar()
        assert bar is not None

    def test_create_with_placeholder(self):
        from widgets.search_bar import SearchBar
        bar = SearchBar(placeholder="Tìm kiếm...")
        assert bar is not None


@pytest.mark.ui
class TestPagination:
    def test_create(self):
        from widgets.pagination import Pagination
        pager = Pagination(total=100, page_size=10)
        assert pager.current_page() == 1
        assert pager.offset() == 0

    def test_set_total(self):
        from widgets.pagination import Pagination
        pager = Pagination(total=0, page_size=10)
        pager.set_total(50)
        assert pager.current_page() == 1

    def test_offset_calculation(self):
        from widgets.pagination import Pagination
        pager = Pagination(total=100, page_size=10)
        # Page 1 → offset 0
        assert pager.offset() == 0
