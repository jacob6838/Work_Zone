import sys
from collections import OrderedDict
sys.path.append('./translator/GCP_cloud_function/cloud_function')
from unittest.mock import MagicMock, patch, call, Mock
sys.modules['icone_translator'] =Mock()
import main
import icone_translator
import os
import json
from unittest import TestCase
import pytest

#delete all the environment variable and make it patch.dict

@patch('urllib.request')
def test_get_ftp_file(request):
    test_url='fake url'
    test_output=main.get_ftp_file(test_url)
    request.urlopen.assert_called_with(test_url)


@patch('google.cloud.pubsub_v1.PublisherClient')
@patch.object(main, 'get_ftp_url')
@patch.object(main, 'get_ftp_file')
@patch.object(main, 'parse_xml')
@patch.object(main, 'get_wzdx_schema')
def test_translate_newest_icone_to_wzdx(get_wzdx_schema, parse_xml, get_ftp_file, get_ftp_url, pubsub):
#the intent of this magic mock fuction is that we give a valid input ,that publishes data
    main.get_ftp_url=MagicMock(return_value='url')
    main.get_ftp_file=MagicMock(return_value='')
    main.parse_xml=MagicMock(return_value='')
    main.get_wzdx_schema=MagicMock(return_value='')
    icone_translator.wzdx_creator= MagicMock(return_value='WZDx')
    icone_translator.validate_wzdx= MagicMock(return_value=True)
    os.environ['project_id']='project_id'
    os.environ['wzdx_topic_id']='wzdx_topic_id'
    main.translate_newest_icone_to_wzdx(None,None)
    publisher=pubsub().publish
    publisher.assert_called_with(pubsub().topic_path('project_id', 'wzdx_topic_id'),str.encode(json.dumps('WZDx', indent=2)),origin='auto_icone_translator_ftp cloud function')


@patch('google.cloud.pubsub_v1.PublisherClient')
@patch.object(main, 'get_ftp_url')
@patch.object(main, 'get_ftp_file')
@patch.object(main, 'parse_xml')
@patch.object(main, 'get_wzdx_schema')
def test_translate_newest_icone_to_wzdx_with_invalid_data(get_wzdx_schema, parse_xml, get_ftp_file, get_ftp_url, pubsub):
#the intent of this magic mock fuction is that we give a valid input ,that publishes data
    main.get_ftp_url=MagicMock(return_value='')
    main.get_ftp_file=MagicMock(return_value='')
    main.parse_xml=MagicMock(return_value='')
    main.get_wzdx_schema=MagicMock(return_value='')
    icone_translator.wzdx_creator= MagicMock(return_value='WZDx')
    icone_translator.validate_wzdx= MagicMock(return_value=False)
    os.environ['project_id']='project_id'
    os.environ['wzdx_topic_id']='wzdx_topic_id'
    main.translate_newest_icone_to_wzdx(None,None)
    publisher=pubsub().publish
    publisher.assert_not_called()



@patch.object(main, 'get_ftp_credentials')
def test_get_ftp_url(ftp_credentials):
    credentials='username', 'password'
    main.get_ftp_credentials=MagicMock(return_value=credentials)
    os.environ['ftp_server_address']='www.icone.com'
    os.environ['ftp_port']='4425'
    os.environ['icone_ftp_username']='username'
    os.environ['icone_ftp_password']='password'
    os.environ['ftp_icone_file_path']='test_filepath'
    test_ftp_url='ftp://username:password@www.icone.com:4425/test_filepath'
    actual=main.get_ftp_url()
    del os.environ['ftp_server_address']
    del os.environ['ftp_port']
    del os.environ['icone_ftp_username']
    del os.environ['icone_ftp_password']
    del os.environ['ftp_icone_file_path']
    assert actual==test_ftp_url

@patch.object(main, 'get_ftp_credentials')
def test_get_ftp_url_missing_environment_variable(ftp_credentials):
    credentials='username', 'password'
    main.get_ftp_credentials=MagicMock(return_value=credentials)
    try:
        actual=main.get_ftp_url()
        assert False
    except KeyError:
        assert True
        
def test_parse_xml():
    test_parse_xml_string= """<incident id="U13631595_202012160845">
        <updatetime>2020-12-16T17:18:00Z</updatetime>
        <type>CONSTRUCTION</type>
         <type> Hazard </type>
          <polyline>34.8380671,-114.1450650,34.8380671,-114.1450650</polyline>
        </incident>"""
    test_valid_output= {"incident": OrderedDict({'@id': 'U13631595_202012160845', 'updatetime': '2020-12-16T17:18:00Z', 'type': ['CONSTRUCTION', 'Hazard'], 'polyline': '34.8380671,-114.1450650,34.8380671,-114.1450650' })}
    actual_output= main.parse_xml(test_parse_xml_string)
    assert actual_output == test_valid_output

@patch.dict(os.environ, {
    'icone_ftp_username_secret_name': 'secret_username',
    'icone_ftp_password_secret_name': 'secret_password',
    'project_id': 'project_id'})
@patch('google.cloud.secretmanager.SecretManagerServiceClient')
def test_get_ftp_credentials(secret):
    secret().access_secret_version = fake_secret_client
    actual = main.get_ftp_credentials()
    valid_username = 'username'
    valid_password = 'password'
    expected = (valid_username, valid_password)
    
    assert actual == expected
    
@patch.dict(os.environ, {})
@patch('google.cloud.secretmanager.SecretManagerServiceClient')
def test_get_ftp_credentials_no_env_vars(secret):
    secret().access_secret_version = fake_secret_client
    actual = main.get_ftp_credentials()
    assert actual == None

@patch.dict(os.environ, {
    'icone_ftp_username_secret_name': 'fail',
    'icone_ftp_password_secret_name': 'secret_password',
    'project_id': 'project_id'})
@patch('google.cloud.secretmanager.SecretManagerServiceClient')
def test_get_ftp_secrets_does_not_exist(secret):
    secret().access_secret_version = fake_secret_client
    actual = main.get_ftp_credentials()
    
    assert actual == (None, None)
    
valid_secret_user_request={"name": "projects/project_id/secrets/secret_username/versions/latest"}
valid_secret_pass_request = {"name": "projects/project_id/secrets/secret_password/versions/latest"}
def fake_secret_client(request):
    if request == valid_secret_user_request:
        username=MagicMock()
        username.payload.data = b'username'
        return username

    elif request == valid_secret_pass_request:
        password=MagicMock()
        password.payload.data = b'password'
        return password

    else:
        raise RuntimeError('secret does not exist!')
        

def test_get_wzdx_schema():
    main.get_wzdx_schema('translator/sample files/validation_schema/wzdx_v3.0_feed.json')
    #wzdx schema will throw an exception if schema is invalid
    assert True

#class get_wzdx_schema(TestCase):
def test_get_wzdx_schema_invalid_data():

    with pytest.raises(RuntimeError) as runtimeErr:
        main.get_wzdx_schema('test/docs/invalid_schema.json')
    assert 'invalid schema: not valid json' in str(runtimeErr.value)

def test_get_wzdx_schema_not_exist():
        
    with pytest.raises(RuntimeError) as runtimeErr:
        main.get_wzdx_schema('not_exist.json')
    assert 'invalid schema: file does not exist' in str(runtimeErr.value)   
    


@patch('google.cloud.pubsub_v1.PublisherClient')
def test_unsupported_messages_callback(pubsub):
    #add one more test: its a valid test,but its another way to test the other published case
    #invalid case
    os.environ['project_id']='project_id'
    os.environ['unsupported_messages_topic_id']='unsupported_messages_topic_id'
    output=main.unsupported_messages_callback('unsupported_messages')
    publisher=pubsub().publish
    publisher.assert_called()

@patch('google.cloud.pubsub_v1.PublisherClient')
def test_unsupported_messages_callback(pubsub):
    #add one more test: its a valid test,but its another way to test the other published case
    #invalid case
    os.environ['project_id']='project_id'
    os.environ['unsupported_messages_topic_id']='unsupported_messages_topic_id'
    output=main.unsupported_messages_callback('unsupported_messages')
    publisher=pubsub().publish
    publisher.assert_called()
    


