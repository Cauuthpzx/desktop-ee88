"""
Unit tests cho server/models.py — Pydantic validation.
"""
import pytest
from pydantic import ValidationError


class TestRegisterReq:
    def test_valid_registration(self):
        from server.models import RegisterReq
        req = RegisterReq(username="alice", password="123456")
        assert req.username == "alice"
        assert req.password == "123456"

    def test_username_too_short(self):
        from server.models import RegisterReq
        with pytest.raises(ValidationError):
            RegisterReq(username="ab", password="123456")

    def test_username_too_long(self):
        from server.models import RegisterReq
        with pytest.raises(ValidationError):
            RegisterReq(username="a" * 101, password="123456")

    def test_password_too_short(self):
        from server.models import RegisterReq
        with pytest.raises(ValidationError):
            RegisterReq(username="alice", password="12345")

    def test_password_too_long(self):
        from server.models import RegisterReq
        with pytest.raises(ValidationError):
            RegisterReq(username="alice", password="a" * 256)

    def test_missing_username(self):
        from server.models import RegisterReq
        with pytest.raises(ValidationError):
            RegisterReq(password="123456")

    def test_missing_password(self):
        from server.models import RegisterReq
        with pytest.raises(ValidationError):
            RegisterReq(username="alice")


class TestLoginReq:
    def test_valid_login(self):
        from server.models import LoginReq
        req = LoginReq(username="admin", password="secret")
        assert req.username == "admin"

    def test_empty_fields_allowed(self):
        """LoginReq không có min_length constraint."""
        from server.models import LoginReq
        req = LoginReq(username="", password="")
        assert req.username == ""


class TestTokenResp:
    def test_success_response(self):
        from server.models import TokenResp
        resp = TokenResp(ok=True, token="jwt123", username="admin", role="admin")
        assert resp.ok is True
        assert resp.token == "jwt123"

    def test_failure_response(self):
        from server.models import TokenResp
        resp = TokenResp(ok=False, message="Invalid credentials")
        assert resp.ok is False
        assert resp.token is None

    def test_optional_fields_default_none(self):
        from server.models import TokenResp
        resp = TokenResp(ok=True)
        assert resp.token is None
        assert resp.username is None
        assert resp.role is None


class TestMsgResp:
    def test_success(self):
        from server.models import MsgResp
        resp = MsgResp(ok=True, message="Done")
        assert resp.ok is True
        assert resp.message == "Done"

    def test_requires_message(self):
        from server.models import MsgResp
        with pytest.raises(ValidationError):
            MsgResp(ok=True)


class TestUpdateProfileReq:
    def test_valid_presence(self):
        from server.models import UpdateProfileReq
        req = UpdateProfileReq(presence="online")
        assert req.presence == "online"

    @pytest.mark.parametrize("status", ["online", "busy", "away", "dnd", "invisible"])
    def test_all_valid_presences(self, status):
        from server.models import UpdateProfileReq
        req = UpdateProfileReq(presence=status)
        assert req.presence == status

    def test_invalid_presence(self):
        from server.models import UpdateProfileReq
        with pytest.raises(ValidationError):
            UpdateProfileReq(presence="unknown")

    def test_all_optional(self):
        from server.models import UpdateProfileReq
        req = UpdateProfileReq()
        assert req.email is None
        assert req.presence is None
        assert req.bio is None


class TestChangePasswordReq:
    def test_valid(self):
        from server.models import ChangePasswordReq
        req = ChangePasswordReq(current_password="old123", new_password="new123")
        assert req.current_password == "old123"

    def test_new_password_too_short(self):
        from server.models import ChangePasswordReq
        with pytest.raises(ValidationError):
            ChangePasswordReq(current_password="old", new_password="12345")


class TestAgentCreateReq:
    def test_valid(self):
        from server.models import AgentCreateReq
        req = AgentCreateReq(name="Bot1", ext_username="bot1")
        assert req.name == "Bot1"
        assert req.ext_password == ""
        assert req.base_url is None

    def test_name_required(self):
        from server.models import AgentCreateReq
        with pytest.raises(ValidationError):
            AgentCreateReq(name="", ext_username="bot1")
