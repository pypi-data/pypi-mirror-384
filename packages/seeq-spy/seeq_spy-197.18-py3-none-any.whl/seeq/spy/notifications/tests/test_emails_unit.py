import json

import pytest

from seeq.spy._errors import SPyValueError
from seeq.spy.notifications._emails import EmailRequestInput, EmailRecipient, EmailAttachment, \
    _create_email_request_input


@pytest.mark.unit
def test_email_recipient():
    recipient1 = EmailRecipient('test1@seeq.com')
    assert recipient1.email == 'test1@seeq.com'
    assert recipient1.name is None

    recipient2 = EmailRecipient(name="alex", email='test2@seeq.com')
    assert recipient2.name == 'alex'
    assert recipient2.email == 'test2@seeq.com'

    with pytest.raises(SPyValueError, match='Invalid email address provided'):
        EmailRecipient("test3")

    with pytest.raises(SPyValueError, match='Invalid email address provided'):
        EmailRecipient("test4", "test5")


@pytest.mark.unit
def test_email_attachment():
    attachment1 = EmailAttachment('content', 'application/pdf', 'sample.pdf')
    assert attachment1.content == 'content'
    assert attachment1.type == 'application/pdf'
    assert attachment1.filename == 'sample.pdf'

    attachment2 = EmailAttachment(filename='sample2.png', content='sample content', type='image/png')
    assert attachment2.content == 'sample content'
    assert attachment2.type == 'image/png'
    assert attachment2.filename == 'sample2.png'

    with pytest.raises(SPyValueError, match='A non-blank attachment content must be provided'):
        EmailAttachment('', 'test1', 'test2')

    with pytest.raises(SPyValueError, match='A non-blank attachment type must be provided'):
        EmailAttachment('test3', ' ', 'test4')

    with pytest.raises(SPyValueError, match='A non-blank attachment filename must be provided'):
        EmailAttachment('test5', 'test6', '  ')


@pytest.mark.unit
def test_email_request_input():
    recipient1 = EmailRecipient('test1@seeq.com')
    email_request_input_1 = EmailRequestInput(toEmails=[recipient1], subject="test subject",
                                              content="<p>Hello World</p>")
    assert json.dumps(email_request_input_1.to_dict()) == \
           '{"toEmails": [{"email": "test1@seeq.com"}], "subject": "test subject", "content": "<p>Hello World</p>"}'

    recipient2 = EmailRecipient('test2@seeq.com')
    recipient3 = EmailRecipient('test3@seeq.com', name="test3name")
    email_request_input_2 = EmailRequestInput(toEmails=[recipient1], ccEmails=[recipient2],
                                              bccEmails=[recipient1, recipient3],
                                              subject="test subject", content="Hello World")
    assert json.dumps(email_request_input_2.to_dict()) == '{"toEmails": [{"email": "test1@seeq.com"}], ' \
                                                          '"subject": "test subject", "content": "Hello World", ' \
                                                          '"ccEmails": [{"email": "test2@seeq.com"}], ' \
                                                          '"bccEmails": [{"email": "test1@seeq.com"}, ' \
                                                          '{"email": "test3@seeq.com", "name": "test3name"}]}'

    email_request_input_3 = EmailRequestInput(toEmails=[recipient1], ccEmails=[], bccEmails=None,
                                              subject="subject", content="content")
    assert email_request_input_3.toEmails == [recipient1]
    assert email_request_input_3.ccEmails == []
    assert email_request_input_3.bccEmails is None

    attachment1 = EmailAttachment(content="gibberish", type="application/pdf", filename="test.pdf")
    email_request_input_4 = EmailRequestInput(toEmails=[recipient1], subject="test subject", content="test content",
                                              attachments=[attachment1])
    assert json.dumps(email_request_input_4.to_dict()) == '{"toEmails": [{"email": "test1@seeq.com"}], ' \
                                                          '"subject": "test subject", ' \
                                                          '"content": "test content", ' \
                                                          '"attachments": [{"content": "gibberish", ' \
                                                          '"type": "application/pdf", ' \
                                                          '"filename": "test.pdf"}]}'

    with pytest.raises(SPyValueError, match='At least one recipient needs to be provided'):
        EmailRequestInput(toEmails=[], subject="some subject", content="some content")

    with pytest.raises(SPyValueError, match='A non blank subject must be provided'):
        EmailRequestInput(toEmails=[recipient1], subject="", content="some content")

    with pytest.raises(SPyValueError, match='A non blank content must be provided'):
        EmailRequestInput(toEmails=[recipient1], subject="some subject", content="")


@pytest.mark.unit
def test_email_request_input_with_reply_to():
    recipient1 = EmailRecipient('test1@seeq.com')
    reply_to_recipient = EmailRecipient('reply@seeq.com', name="Reply Name")

    # Test basic reply-to functionality
    email_request_input_1 = EmailRequestInput(toEmails=[recipient1], subject="test subject",
                                              content="<p>Hello World</p>", replyToEmails=[reply_to_recipient])
    assert email_request_input_1.replyToEmails == [reply_to_recipient]

    # Test reply-to in JSON serialization
    expected_json = '{"toEmails": [{"email": "test1@seeq.com"}], "subject": "test subject", "content": "<p>Hello World</p>", "replyToEmails": [{"email": "reply@seeq.com", "name": "Reply Name"}]}'
    assert json.dumps(email_request_input_1.to_dict()) == expected_json

    # Test reply-to with string email
    reply_to_string = EmailRecipient('reply2@seeq.com')
    email_request_input_2 = EmailRequestInput(toEmails=[recipient1], subject="test subject",
                                              content="Hello World", replyToEmails=[reply_to_string])
    assert email_request_input_2.replyToEmails == [reply_to_string]

    # Test reply-to with None (should be allowed)
    email_request_input_3 = EmailRequestInput(toEmails=[recipient1], subject="test subject",
                                              content="Hello World", replyToEmails=None)
    assert email_request_input_3.replyToEmails is None

    # Test reply-to with empty list (should be allowed)
    email_request_input_4 = EmailRequestInput(toEmails=[recipient1], subject="test subject",
                                              content="Hello World", replyToEmails=[])
    assert email_request_input_4.replyToEmails == []


@pytest.mark.unit
def test_email_request_input_reply_to_validation():
    recipient1 = EmailRecipient('test1@seeq.com')
    reply_to_recipient1 = EmailRecipient('reply1@seeq.com')
    reply_to_recipient2 = EmailRecipient('reply2@seeq.com')

    # Test that multiple reply-to emails are not allowed
    with pytest.raises(SPyValueError, match='Only one reply-to email address is currently allowed'):
        EmailRequestInput(toEmails=[recipient1], subject="test subject", content="Hello World",
                          replyToEmails=[reply_to_recipient1, reply_to_recipient2])

    # Test that single reply-to email is allowed
    email_request_input = EmailRequestInput(toEmails=[recipient1], subject="test subject", content="Hello World",
                                            replyToEmails=[reply_to_recipient1])
    assert email_request_input.replyToEmails == [reply_to_recipient1]


@pytest.mark.unit
def test_create_email_request_input_with_reply_to():
    # Test string reply-to
    email_input = _create_email_request_input(
        to="test@seeq.com",
        subject="Test Subject",
        content="Test Content",
        cc=None,
        bcc=None,
        attachments=None,
        reply_to="reply@seeq.com"
    )
    assert len(email_input.replyToEmails) == 1
    assert email_input.replyToEmails[0].email == "reply@seeq.com"
    assert email_input.replyToEmails[0].name is None

    # Test EmailRecipient reply-to
    reply_recipient = EmailRecipient("reply2@seeq.com", name="Reply Name")
    email_input2 = _create_email_request_input(
        to="test@seeq.com",
        subject="Test Subject",
        content="Test Content",
        cc=None,
        bcc=None,
        attachments=None,
        reply_to=reply_recipient
    )
    assert email_input2.replyToEmails == [reply_recipient]

    # Test list of strings reply-to
    email_input3 = _create_email_request_input(
        to="test@seeq.com",
        subject="Test Subject",
        content="Test Content",
        cc=None,
        bcc=None,
        attachments=None,
        reply_to=["reply3@seeq.com"]
    )
    assert len(email_input3.replyToEmails) == 1
    assert email_input3.replyToEmails[0].email == "reply3@seeq.com"

    # Test None reply-to
    email_input4 = _create_email_request_input(
        to="test@seeq.com",
        subject="Test Subject",
        content="Test Content",
        cc=None,
        bcc=None,
        attachments=None,
        reply_to=None
    )
    assert email_input4.replyToEmails is None

    # Test that multiple reply-to emails are rejected by validation
    with pytest.raises(SPyValueError, match='Only one reply-to email address is currently allowed'):
        _create_email_request_input(
            to="test@seeq.com",
            subject="Test Subject",
            content="Test Content",
            cc=None,
            bcc=None,
            attachments=None,
            reply_to=["reply1@seeq.com", "reply2@seeq.com"]
        )
