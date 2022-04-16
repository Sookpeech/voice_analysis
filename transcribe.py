from msilib.schema import Media
from urllib import request
from ast import literal_eval
import boto3
from botocore.config import Config

def transcribe_wav_file(wav_file_title, wav_file_path):
    bucket_name = "sookpeech-wavfile"

    # upload wav file to s3
    audio = open('{}{}.wav'.format(wav_file_path, wav_file_title), 'rb')
    s3 = boto3.resource('s3')
    upload = s3.Bucket(bucket_name).put_object(Key="{}.wav".format(wav_file_title), Body=audio)

    # Config for transcribe
    my_config = Config(
        region_name = 'ap-northeast-2',
        signature_version = 'v4',
        retries={
            'max_attempts': 5,
            'mode' : 'standard'
        }
    )

    # run transcribe
    transcribe = boto3.client('transcribe', config=my_config)
    job_uri = 'https://s3.ap-northeast-2.amazonaws.com/{}/{}.wav'.format(bucket_name, wav_file_title)
    transcribe.start_transcription_job(
        TranscriptionJobName = wav_file_title,
        Media={'MediaFileUri': job_uri},
        MediaFormat='wav',
        LanguageCode = 'ko-KR',
        Settings={
            'ShowSpeakerLabels': False
        }
    )

    # check transcription compeleted or failed
    while True:
        status = transcribe.get_transcription_job(TranscriptionJobName = wav_file_title)
        if status['TranscriptionJob']['TranscriptionJobStatus'] in ['COMPLETED', 'FAILED']:
            save_json_uri = status['TranscriptionJob']['Transcript']['TranscriptFileUri']
            break
    save_json_uri = status['TranscriptionJob']['Transcript']['TranscriptFileUri']

    # browse transcribe result
    load = request.urlopen(save_json_uri)
    confirm = load.status
    result = load.read().decode('utf-8')
    result_text = literal_eval(result)['results']['transcripts'][0]['transcript']

    print(result_text)

    # delete transcribe job
    # when you start to run transcribe on the same job-name, it will evoke Badrequest error
    delete_transcribe = boto3.client('transcribe', config=my_config)
    res = delete_transcribe.delete_transcription_job(
        TranscriptionJobName = wav_file_title
    ) 

    res['ResponseMetadata']['HTTPStatusCode']=='200'