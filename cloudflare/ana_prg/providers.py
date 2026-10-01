"""Secret-backed providers. No automatic retry of ambiguous external effects."""
import base64, json, os, urllib.request, urllib.error

class ProviderError(RuntimeError):
    def __init__(self,code,ambiguous=False,raw=None):
        super().__init__(code);self.ambiguous=ambiguous;self.raw=raw

class OpenAI:
    def read(self, *, model, prompt, schema, data, mime, request_id):
        key=os.environ.get('OPENAI_API_KEY')
        if not key: raise ProviderError('OPENAI_CREDENTIAL_MISSING')
        encoded=base64.b64encode(data).decode()
        attachment={'type':'input_image','image_url':f'data:{mime};base64,{encoded}','detail':'high'}
        if mime=='application/pdf':
            attachment={'type':'input_file','filename':'ana-input.pdf','file_data':f'data:application/pdf;base64,{encoded}'}
        body={'model':model,'store':False,'reasoning':{'effort':'medium'},'max_output_tokens':12000,
              'input':[{'role':'user','content':[{'type':'input_text','text':prompt},attachment]}],
              'text':{'format':{'type':'json_schema','name':'ana_answers','strict':True,'schema':schema}}}
        req=urllib.request.Request('https://api.openai.com/v1/responses',data=json.dumps(body).encode(),
            headers={'Authorization':'Bearer '+key,'Content-Type':'application/json','X-Client-Request-Id':request_id})
        try:
            with urllib.request.urlopen(req,timeout=180) as r: raw=json.load(r)
        except urllib.error.HTTPError as e:
            raise ProviderError('OPENAI_HTTP_'+str(e.code),ambiguous=e.code>=500) from None
        except (TimeoutError,OSError): raise ProviderError('OPENAI_NETWORK_UNCERTAIN',True) from None
        if raw.get('status')!='completed': raise ProviderError('OPENAI_INCOMPLETE_RESPONSE',raw=raw)
        text=[]
        for output in raw.get('output',[]):
            for content in output.get('content',[]):
                if content.get('type')=='refusal': raise ProviderError('OPENAI_REFUSAL',raw=raw)
                if content.get('type')=='output_text': text.append(content['text'])
        try: normalized=json.loads(''.join(text))
        except (ValueError,TypeError): raise ProviderError('OPENAI_INVALID_JSON',raw=raw) from None
        return normalized,raw

class MetaWhatsApp:
    def send(self, *, phone, template, language, parameters, request_id):
        key=os.environ.get('ANA_WHATSAPP_ACCESS_TOKEN');phone_id=os.environ.get('ANA_WHATSAPP_PHONE_NUMBER_ID')
        if not key or not phone_id: raise ProviderError('WHATSAPP_CREDENTIAL_MISSING')
        version=os.environ.get('ANA_WHATSAPP_API_VERSION','v23.0')
        body={'messaging_product':'whatsapp','to':phone.lstrip('+'),'type':'template',
              'template':{'name':template,'language':{'code':language},'components':[]},'biz_opaque_callback_data':request_id}
        if parameters: body['template']['components']=[{'type':'body','parameters':[{'type':'text','text':str(p)} for p in parameters]}]
        req=urllib.request.Request(f'https://graph.facebook.com/{version}/{phone_id}/messages',data=json.dumps(body).encode(),
            headers={'Authorization':'Bearer '+key,'Content-Type':'application/json'})
        try:
            with urllib.request.urlopen(req,timeout=40) as r: raw=json.load(r)
        except urllib.error.HTTPError as e:
            raise ProviderError('WHATSAPP_HTTP_'+str(e.code),e.code>=500) from None
        except (TimeoutError,OSError): raise ProviderError('WHATSAPP_NETWORK_UNCERTAIN',True) from None
        message=(raw.get('messages') or [{}])[0].get('id')
        if not message: raise ProviderError('WHATSAPP_DELIVERY_UNCERTAIN',True)
        return message

def answer_schema(subjects,allow_blank=True):
    return {'type':'object','additionalProperties':False,'required':['answers','confidence','feedback'],
        'properties':{'answers':{'type':'array','items':{'type':'object','additionalProperties':False,
            'required':['subject','question_no','answer'],'properties':{
                'subject':{'type':'string','enum':subjects},'question_no':{'type':'integer'},
                'answer':{'type':'string','enum':['A','B','C','D','E']+([''] if allow_blank else [])}}}},
            'confidence':{'type':'number'},'feedback':{'type':'string'}}}
