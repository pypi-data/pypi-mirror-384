from unittest import IsolatedAsyncioTestCase

from ....did.did_key import DIDKey
from ....protocols.didexchange.v1_0.messages.request import DIDXRequest
from ....protocols.out_of_band.v1_0.messages.invitation import InvitationMessage
from ....protocols.out_of_band.v1_0.messages.service import Service
from ....storage.base import BaseStorage
from ....storage.error import StorageNotFoundError
from ....utils.testing import create_test_profile
from ....wallet.key_type import ED25519
from ..conn_record import ConnRecord


class TestConnRecord(IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.profile = await create_test_profile()

        self.test_seed = "testseed000000000000000000000001"
        self.test_did = "55GkHamhTU1ZbTbV2ab9DE"
        self.test_verkey = "3Dn1SJNPaCXcvvJvSbsFWP2xaCjMom3can8CQNhWrTRx"
        self.test_endpoint = "http://localhost"

        self.test_target_did = "GbuDUYXaUZRfHD2jeDuQuP"
        self.test_target_verkey = "9WCgWKUaAJj3VWxxtzvvMQN3AoFxoBtBDo9ntwJnVVCC"

        self.test_did_peer_4_a = "did:peer:4zQmV3Hf1TT4Xn73MBVf2NAWdMwrzUabpEvwtV3RoZc17Vxr:z2pfttj3xn6tJ7wpHV9ZSwpQVMNtHC7EtM36r1mC5fDpZ25882Yitk21QPbqzuefKPrbFsexWmQtE78vYWweckXtKeu5BhuFDvCjMUf8SC5z7cMPvp8SCdcbqWnHxygjBH9zAAs9myGRnZYXuAkq6CfBdn6ZiNmdRf65TdVfE3cYfS4jNzVZDs1abwytn4jdFJ2fwVegPB3vLY8XxeUEx12a4rtjkqMhs6zBQbJvc4PVUM9rvMbPM2QeXDy7ovkkHaKLUbNUxjQrcQeiR8MTLe1iaVtUv6RpBf4z7ioqfa4VDRmAZT7isVM3NvENUceeUfDZoFbM8PZqGkCbFvfoKiK3SrmTsvPtpXaBAfR4z7w18cFjsvvLBNMZbPnARn4oZijCkYwgaNmAUthgDP4XBFetdUo8728w25FUwTWjAPc1BdSSWPWMRKwCqyAP1Q1hM8dU6otT27MQaQ1rozKncn3U48CXEi2Ef26EDBrSozEWR273ancFojNXBbZVghZG5b6xdypjQir9PgTF94dsygtu47hNxQweVKLUM1p9umqHLhjvLhpS1aGQkGZNnKUHjLDHdToigo15F7TAf8RfMaducHBThFzEp9TUJmiZFTUYQ1uaBgSPMSaWnvTfUoFmLoGbdrWj1vVEsRrARq37u1SJGLqBx7FM2SUd8nxPsChP5jY8ka8F8r7j8qZLHZqvUXbynPUsViwwdFFk8SCsBWfiQgvq7sRiTdLnYv3H5DSwA1uW2GNYXGgkT9aJza4Sk1gvag5iAbQZgxbU594enjVSTjiWsFw2oYQ75JJwiSEgsP2rhpGsNhXxfECNLUtb7FQbDQPtUvLHCJATf7QXJEoWjpfAywmB6NyQcXfskco6FKJNNHeZBnST6U1meH98Ku66vha1k8hAc72iBhXQBnWUjaGRyzELsh2LkBH2UNwW9TuFhxz3SKtL5pGShVQ5XGQhmdrkWP68d6h7c1JqsfogcDBnmWS4VSbJwgtsPNTSsTHGX8hpGvg"
        self.test_did_peer_4_short_a = (
            "did:peer:4zQmV3Hf1TT4Xn73MBVf2NAWdMwrzUabpEvwtV3RoZc17Vxr"
        )
        self.test_did_peer_4_b = "did:peer:4zQmQ4dEtoGcivpiH6gtWwhWJY2ENVWuZifb62uzR76HGPPw:z7p4QX8zEXt2sMjv1Tqq8Lv8Nx8oGo2uRczBe21vyfMhQzsWDnwGmjriYfUX75WDq622czcdHjWGhh2VTbzKhLXUjY8Ma7g64dKAVcy8SaxN5QVdjwpXgD7htKCgCjah8jHEzyBZFrtdfTHiVXfSUz1BiURQf1Z3NfxW5cWYsvDJVvQzVmdHb8ekzCnvxCqL2UV1v9SBb1DsU66N3PCp9HVpSrqUJQyFU2Ddc8bb6u8SJfBU1nyCkNMgfA1zAyKnSBrzZWyyNzAm9oBV36qjC1Qjfcpq4FBnGr7foh5sLXppBwu2ES8U2nxdGrQzAbN47DKBoKJqPVxNh5tTuBdYjDGt7PcvZQjHQGNXXuhJctM5besZci2saGefCHzoZ87vSsFuKq6oXEsW512eadiNZWjHSdG9J4ToMEMK9WT66vGGLFdZszB3xhdFqEDnAMcpnoFUL5WN243aH6492jPC2Zjdi1BvHC1J8bUuvyihAKXF3WmFz7gJWmh6MrTEWNqb17K6tqbyXjFmfnS2RbAi8xBFj3sSsXkSs6TRTXAZD9DenYaQq4RMa2Kqh6VKGvkXAjVHKcPh9Ncpt6rU9ZYttNHbDJFgahwB8KisVBK8FBpG"
        self.test_did_peer_4_short_b = (
            "did:peer:4zQmQ4dEtoGcivpiH6gtWwhWJY2ENVWuZifb62uzR76HGPPw"
        )
        self.test_did_key = DIDKey.from_public_key_b58(self.test_verkey, ED25519)

        self.test_conn_record = ConnRecord(
            my_did=self.test_did,
            their_did=self.test_target_did,
            their_role=ConnRecord.Role.REQUESTER.rfc23,
            state=ConnRecord.State.COMPLETED.rfc23,
        )
        assert self.test_conn_record.their_role == ConnRecord.Role.REQUESTER.rfc160
        assert self.test_conn_record.state == ConnRecord.State.COMPLETED.rfc160
        assert self.test_conn_record.rfc23_state == ConnRecord.State.COMPLETED.rfc23

    async def test_get_enums(self):
        assert ConnRecord.Role.get("Larry") is None
        assert ConnRecord.State.get("a suffusion of yellow") is None

        assert ConnRecord.Role.get(ConnRecord.Role.REQUESTER) is ConnRecord.Role.REQUESTER

        assert (
            ConnRecord.State.get(ConnRecord.State.RESPONSE) is ConnRecord.State.RESPONSE
        )

        assert ConnRecord.Role.REQUESTER.flip() is ConnRecord.Role.RESPONDER
        assert ConnRecord.Role.get(
            ConnRecord.Role.REQUESTER.rfc160
        ) is ConnRecord.Role.get(ConnRecord.Role.REQUESTER.rfc23)
        assert ConnRecord.Role.REQUESTER == ConnRecord.Role.REQUESTER.rfc160  # check ==
        assert ConnRecord.Role.REQUESTER == ConnRecord.Role.REQUESTER.rfc23
        assert ConnRecord.Role.REQUESTER != ConnRecord.Role.RESPONDER.rfc23

    async def test_state_rfc23strict(self):
        for state in (
            ConnRecord.State.INIT,
            ConnRecord.State.ABANDONED,
            ConnRecord.State.COMPLETED,
        ):
            assert state.rfc23strict(their_role=None) == state.value[1]

        for state in (ConnRecord.State.INVITATION, ConnRecord.State.RESPONSE):
            assert (
                state.rfc23strict(their_role=ConnRecord.Role.REQUESTER)
                == f"{state.value[1]}-sent"
            )
            assert (
                state.rfc23strict(their_role=ConnRecord.Role.RESPONDER)
                == f"{state.value[1]}-received"
            )

        assert (
            ConnRecord.State.REQUEST.rfc23strict(their_role=ConnRecord.Role.REQUESTER)
            == f"{ConnRecord.State.REQUEST.value[1]}-received"
        )
        assert (
            ConnRecord.State.REQUEST.rfc23strict(their_role=ConnRecord.Role.RESPONDER)
            == f"{ConnRecord.State.REQUEST.value[1]}-sent"
        )

    async def test_save_retrieve_compare(self):
        record = ConnRecord(my_did=self.test_did)
        async with self.profile.session() as session:
            connection_id = await record.save(session)
            fetched = await ConnRecord.retrieve_by_id(session, connection_id)
            assert fetched and fetched == record

            bad_record = ConnRecord(my_did=None)
            bad_record._id = record._id
            bad_record.created_at = record.created_at
            bad_record.updated_at = record.updated_at
            assert bad_record != record

            record = ConnRecord(
                state=ConnRecord.State.INIT,  # exercise init State by enum
                my_did=self.test_did,
                their_role=ConnRecord.Role.REQUESTER,  # exercise init Role by enum
            )
            connection_id = await record.save(session)
            fetched = await ConnRecord.retrieve_by_id(session, connection_id)
            assert fetched and fetched == record
            assert fetched.state is ConnRecord.State.INIT.rfc160
            assert ConnRecord.State.get(fetched.state) is ConnRecord.State.INIT
            assert fetched.their_role is ConnRecord.Role.REQUESTER.rfc160
            assert ConnRecord.Role.get(fetched.their_role) is ConnRecord.Role.REQUESTER

            record160 = ConnRecord(
                state=ConnRecord.State.INIT.rfc23,
                my_did=self.test_did,
                their_role=ConnRecord.Role.REQUESTER.rfc23,
            )
            record160._id = record._id
            record160.created_at = record.created_at
            record160.updated_at = record.updated_at
            assert record160 == record

    async def test_retrieve_by_did(self):
        async with self.profile.session() as session:
            record = ConnRecord(
                my_did=self.test_did,
                their_did=self.test_target_did,
                their_role=ConnRecord.Role.RESPONDER.rfc23,
                state=ConnRecord.State.COMPLETED.rfc23,
            )
            await record.save(session)
            result = await ConnRecord.retrieve_by_did(
                session=session,
                my_did=self.test_did,
                their_did=self.test_target_did,
                their_role=ConnRecord.Role.RESPONDER.rfc160,
            )
            assert result == record

    async def test_retrieve_by_did_peer_4_by_long(self):
        async with self.profile.session() as session:
            record = ConnRecord(
                my_did=self.test_did,
                their_did=self.test_did_peer_4_a,
                their_role=ConnRecord.Role.RESPONDER.rfc23,
                state=ConnRecord.State.COMPLETED.rfc23,
            )
            await record.save(session)
            result = await ConnRecord.retrieve_by_did_peer_4(
                session=session,
                my_did=self.test_did,
                their_did_long=self.test_did_peer_4_a,
                their_role=ConnRecord.Role.RESPONDER.rfc160,
            )
            assert result == record

    async def test_retrieve_by_did_peer_4_by_short(self):
        async with self.profile.session() as session:
            record = ConnRecord(
                my_did=self.test_did,
                their_did=self.test_did_peer_4_short_b,
                their_role=ConnRecord.Role.RESPONDER.rfc23,
                state=ConnRecord.State.COMPLETED.rfc23,
            )
            await record.save(session)
            result = await ConnRecord.retrieve_by_did_peer_4(
                session=session,
                my_did=self.test_did,
                their_did_short=self.test_did_peer_4_short_b,
                their_role=ConnRecord.Role.RESPONDER.rfc160,
            )
            assert result == record

    async def test_retrieve_by_did_peer_4_by_either(self):
        async with self.profile.session() as session:
            record_short = ConnRecord(
                my_did=self.test_did,
                their_did=self.test_did_peer_4_short_a,
                their_role=ConnRecord.Role.RESPONDER.rfc23,
                state=ConnRecord.State.COMPLETED.rfc23,
            )
            await record_short.save(session)
            record_long = ConnRecord(
                my_did=self.test_did,
                their_did=self.test_did_peer_4_b,
                their_role=ConnRecord.Role.RESPONDER.rfc23,
                state=ConnRecord.State.COMPLETED.rfc23,
            )
            await record_long.save(session)

            result = await ConnRecord.retrieve_by_did_peer_4(
                session=session,
                my_did=self.test_did,
                their_did_short=self.test_did_peer_4_short_a,
                their_did_long=self.test_did_peer_4_a,
                their_role=ConnRecord.Role.RESPONDER.rfc160,
            )
            assert result == record_short
            result = await ConnRecord.retrieve_by_did_peer_4(
                session=session,
                my_did=self.test_did,
                their_did_short=self.test_did_peer_4_short_b,
                their_did_long=self.test_did_peer_4_b,
                their_role=ConnRecord.Role.RESPONDER.rfc160,
            )
            assert result == record_long

    async def test_from_storage_with_initiator_old(self):
        record = ConnRecord(my_did=self.test_did, state=ConnRecord.State.COMPLETED)
        ser = record.serialize()
        ser["initiator"] = "self"  # old-style ConnectionRecord
        ConnRecord.from_storage("conn-id", ser)

    async def test_retrieve_by_invitation_key(self):
        async with self.profile.session() as session:
            record = ConnRecord(
                my_did=self.test_did,
                their_did=self.test_target_did,
                their_role=ConnRecord.Role.RESPONDER.rfc160,
                state=ConnRecord.State.INVITATION.rfc23,
                invitation_key="dummy",
            )
            await record.save(session)
            result = await ConnRecord.retrieve_by_invitation_key(
                session=session,
                invitation_key="dummy",
                their_role=ConnRecord.Role.RESPONDER.rfc23,
            )
            assert result == record
            with self.assertRaises(StorageNotFoundError):
                await ConnRecord.retrieve_by_invitation_key(
                    session=session,
                    invitation_key="dummy",
                    their_role=ConnRecord.Role.REQUESTER.rfc23,
                )

    async def test_retrieve_by_invitation_msg_id(self):
        async with self.profile.session() as session:
            record = ConnRecord(
                my_did=self.test_did,
                their_did=self.test_target_did,
                their_role=ConnRecord.Role.RESPONDER.rfc160,
                state=ConnRecord.State.INVITATION.rfc160,
                invitation_msg_id="test123",
            )
            await record.save(session)
            result = await ConnRecord.retrieve_by_invitation_msg_id(
                session=session,
                invitation_msg_id="test123",
                their_role=ConnRecord.Role.RESPONDER.rfc160,
            )
            assert result
            assert result == record
            result = await ConnRecord.retrieve_by_invitation_msg_id(
                session=session,
                invitation_msg_id="test123",
                their_role=ConnRecord.Role.REQUESTER.rfc160,
            )
            assert not result

    async def test_find_existing_connection(self):
        async with self.profile.session() as session:
            record_a = ConnRecord(
                my_did=self.test_did,
                their_did=self.test_target_did,
                their_role=ConnRecord.Role.RESPONDER.rfc160,
                state=ConnRecord.State.COMPLETED.rfc160,
                invitation_msg_id="test123",
                their_public_did="test_did_1",
            )
            await record_a.save(session)
            record_b = ConnRecord(
                my_did=self.test_did,
                their_did=self.test_target_did,
                their_role=ConnRecord.Role.RESPONDER.rfc160,
                state=ConnRecord.State.INVITATION.rfc160,
                invitation_msg_id="test123",
                their_public_did="test_did_1",
            )
            await record_b.save(session)
            record_c = ConnRecord(
                my_did=self.test_did,
                their_did=self.test_target_did,
                their_role=ConnRecord.Role.RESPONDER.rfc160,
                state=ConnRecord.State.COMPLETED.rfc160,
                invitation_msg_id="test123",
            )
            await record_c.save(session)
            result = await ConnRecord.find_existing_connection(
                session=session,
                their_public_did="test_did_1",
            )
            assert result
            assert result.state == "active"
            assert result.their_public_did == "test_did_1"

    async def test_retrieve_by_request_id(self):
        async with self.profile.session() as session:
            record = ConnRecord(
                my_did=self.test_did,
                their_did=self.test_target_did,
                their_role=ConnRecord.Role.RESPONDER.rfc23,
                state=ConnRecord.State.COMPLETED.rfc23,
                request_id="abc123",
            )
            await record.save(session)
            result = await ConnRecord.retrieve_by_request_id(
                session=session, request_id="abc123"
            )
            assert result == record

    async def test_completed_is_ready(self):
        async with self.profile.session() as session:
            record = ConnRecord(my_did=self.test_did, state=ConnRecord.State.COMPLETED)
            connection_id = await record.save(session)
            fetched = await ConnRecord.retrieve_by_id(session, connection_id)

        assert fetched.is_ready is True

    async def test_response_is_ready(self):
        async with self.profile.session() as session:
            record = ConnRecord(my_did=self.test_did, state=ConnRecord.State.RESPONSE)
            connection_id = await record.save(session)
            fetched = await ConnRecord.retrieve_by_id(session, connection_id)

            assert fetched.is_ready is True

    async def test_request_is_not_ready(self):
        async with self.profile.session() as session:
            record = ConnRecord(my_did=self.test_did, state=ConnRecord.State.REQUEST)
            connection_id = await record.save(session)
            fetched = await ConnRecord.retrieve_by_id(session, connection_id)

            assert fetched.is_ready is False

    async def test_invitation_is_not_multi_use(self):
        async with self.profile.session() as session:
            record = ConnRecord(
                my_did=self.test_did,
                state=ConnRecord.State.INVITATION.rfc23,
                invitation_mode=ConnRecord.INVITATION_MODE_ONCE,
            )
            connection_id = await record.save(session)
            fetched = await ConnRecord.retrieve_by_id(session, connection_id)

        assert fetched.is_multiuse_invitation is False

    async def test_invitation_is_multi_use(self):
        async with self.profile.session() as session:
            record = ConnRecord(
                my_did=self.test_did,
                state=ConnRecord.State.INVITATION.rfc23,
                invitation_mode=ConnRecord.INVITATION_MODE_MULTI,
            )
            connection_id = await record.save(session)
            fetched = await ConnRecord.retrieve_by_id(session, connection_id)

            assert fetched.is_multiuse_invitation is True

    async def test_attach_retrieve_invitation(self):
        async with self.profile.session() as session:
            record = ConnRecord(
                my_did=self.test_did,
                state=ConnRecord.State.INVITATION.rfc23,
            )
            await record.save(session)

            service = Service(
                _id="asdf",
                _type="did-communication",
                recipient_keys=[self.test_did_key.did],
                service_endpoint="http://localhost:8999",
            )
            invi = InvitationMessage(
                handshake_protocols=["didexchange/1.1"],
                services=[service],
                label="abc123",
            )
            await record.attach_invitation(session, invi)
            retrieved = await record.retrieve_invitation(session)
            assert isinstance(retrieved, InvitationMessage)

    async def test_attach_retrieve_request(self):
        async with self.profile.session() as session:
            record = ConnRecord(
                my_did=self.test_did,
                state=ConnRecord.State.INVITATION.rfc23,
            )
            await record.save(session)

            req = DIDXRequest(
                did=self.test_did,
                label="abc123",
            )
            await record.attach_request(session, req)
            retrieved = await record.retrieve_request(session)
            assert isinstance(retrieved, DIDXRequest)

    async def test_attach_request_abstain_on_alien_deco(self):
        async with self.profile.session() as session:
            record = ConnRecord(
                my_did=self.test_did,
                state=ConnRecord.State.INVITATION.rfc23,
            )
            await record.save(session)

            req = DIDXRequest(
                did=self.test_did,
                label="abc123",
            )
            ser = req.serialize()
            ser["~alien"] = [
                {"nickname": "profile-image", "data": {"links": ["face.png"]}}
            ]
            alien_req = DIDXRequest.deserialize(ser)
            await record.attach_request(session, alien_req)
            alien_ser = alien_req.serialize()
            assert "~alien" in alien_ser

            ser["~alien"] = None
            alien_req = DIDXRequest.deserialize(ser)
            await record.attach_request(session, alien_req)
            alien_ser = alien_req.serialize()
            assert "~alien" not in alien_ser

    async def test_ser_rfc23_state_present(self):
        record = ConnRecord(
            state=ConnRecord.State.INVITATION,
            my_did=self.test_did,
            their_role=ConnRecord.Role.REQUESTER,
        )
        ser = record.serialize()
        assert ser["rfc23_state"] == f"{ConnRecord.State.INVITATION.value[1]}-sent"

    async def test_deser_old_style_record(self):
        record = ConnRecord(
            state=ConnRecord.State.INIT,
            my_did=self.test_did,
            their_role=ConnRecord.Role.REQUESTER,
        )
        ser = record.serialize()
        ser["initiator"] = "self"  # redundant vs. role as per RFC 160 or RFC 23
        deser = ConnRecord.deserialize(ser)
        reser = deser.serialize()
        assert "initiator" not in reser

    async def test_deserialize_connection_protocol(self):
        record = ConnRecord(
            state=ConnRecord.State.INIT,
            my_did=self.test_did,
            their_role=ConnRecord.Role.REQUESTER,
            connection_protocol="didexchange/1.0",
        )
        ser = record.serialize()
        deser = ConnRecord.deserialize(ser)
        assert deser.connection_protocol == "didexchange/1.0"

    async def test_metadata_set_get(self):
        async with self.profile.session() as session:
            record = ConnRecord(
                my_did=self.test_did,
            )
            await record.save(session)
            await record.metadata_set(session, "key", {"test": "value"})
            retrieved = await record.metadata_get(session, "key")
            assert retrieved == {"test": "value"}

    async def test_metadata_set_get_str(self):
        async with self.profile.session() as session:
            record = ConnRecord(
                my_did=self.test_did,
            )
            await record.save(session)
            await record.metadata_set(session, "key", "value")
            retrieved = await record.metadata_get(session, "key")
            assert retrieved == "value"

    async def test_metadata_set_update_get(self):
        async with self.profile.session() as session:
            record = ConnRecord(
                my_did=self.test_did,
            )
            await record.save(session)
            await record.metadata_set(session, "key", {"test": "value"})
            await record.metadata_set(session, "key", {"test": "updated"})
            retrieved = await record.metadata_get(session, "key")
            assert retrieved == {"test": "updated"}

    async def test_metadata_get_without_set_is_none(self):
        async with self.profile.session() as session:
            record = ConnRecord(
                my_did=self.test_did,
            )
            await record.save(session)
            assert await record.metadata_get(session, "key") is None

    async def test_metadata_get_default(self):
        async with self.profile.session() as session:
            record = ConnRecord(
                my_did=self.test_did,
            )
            await record.save(session)
            assert await record.metadata_get(session, "key", {"test": "default"}) == {
                "test": "default"
            }

    async def test_metadata_set_delete_get_is_none(self):
        async with self.profile.session() as session:
            record = ConnRecord(
                my_did=self.test_did,
            )
            await record.save(session)
            await record.metadata_set(session, "key", {"test": "value"})
            await record.metadata_delete(session, "key")
            assert await record.metadata_get(session, "key") is None

    async def test_metadata_delete_without_set_raise_error(self):
        async with self.profile.session() as session:
            record = ConnRecord(
                my_did=self.test_did,
            )
            await record.save(session)
            with self.assertRaises(KeyError):
                await record.metadata_delete(session, "key")

    async def test_metadata_get_all(self):
        async with self.profile.session() as session:
            record = ConnRecord(
                my_did=self.test_did,
            )
            await record.save(session)
            await record.metadata_set(session, "key", {"test": "value"})
            await record.metadata_set(session, "key", {"test": "updated"})
            await record.metadata_set(session, "other", {"test": "other"})
            retrieved = await record.metadata_get_all(session)
            assert retrieved == {"key": {"test": "updated"}, "other": {"test": "other"}}

    async def test_metadata_get_all_without_set_is_empty(self):
        async with self.profile.session() as session:
            record = ConnRecord(
                my_did=self.test_did,
            )
            await record.save(session)
            assert await record.metadata_get_all(session) == {}

    async def test_delete_conn_record_deletes_metadata(self):
        async with self.profile.session() as session:
            record = ConnRecord(
                my_did=self.test_did,
            )
            await record.save(session)
            await record.metadata_set(session, "key", {"test": "value"})
            await record.delete_record(session)
            storage = session.inject(BaseStorage)
            assert (
                await storage.find_all_records(
                    ConnRecord.RECORD_TYPE_METADATA,
                    {"connection_id": record.connection_id},
                )
                == []
            )
