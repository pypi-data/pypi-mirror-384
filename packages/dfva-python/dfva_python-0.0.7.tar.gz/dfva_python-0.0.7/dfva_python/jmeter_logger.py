from urllib.parse import urlparse
import json
DATA = []

def add_jmetter_server(settings, name, url, parameters):

  o = urlparse(url)

  data = {
    'name': name,
   'protocol': o.scheme,
   'domain': o.hostname,
    'url': o.path,
    'port': o.port or '443',
    'data': json.dumps(parameters)
  }
  new_data = """
 <HTTPSamplerProxy guiclass="HttpTestSampleGui" testclass="HTTPSamplerProxy" testname="%(name)s" enabled="true">
          <boolProp name="HTTPSampler.postBodyRaw">true</boolProp>
          <elementProp name="HTTPsampler.Arguments" elementType="Arguments">
            <collectionProp name="Arguments.arguments">
              <elementProp name="" elementType="HTTPArgument">
                <boolProp name="HTTPArgument.always_encode">false</boolProp>
                <stringProp name="Argument.value">%(data)s</stringProp>
                <stringProp name="Argument.metadata">=</stringProp>
              </elementProp>
            </collectionProp>
          </elementProp>
          <stringProp name="HTTPSampler.domain">%(domain)s</stringProp>
          <stringProp name="HTTPSampler.port">%(port)s</stringProp>
          <stringProp name="HTTPSampler.protocol">%(protocol)s</stringProp>
          <stringProp name="HTTPSampler.contentEncoding"></stringProp>
          <stringProp name="HTTPSampler.path">%(url)s</stringProp>
          <stringProp name="HTTPSampler.method">POST</stringProp>
          <boolProp name="HTTPSampler.follow_redirects">true</boolProp>
          <boolProp name="HTTPSampler.auto_redirects">false</boolProp>
          <boolProp name="HTTPSampler.use_keepalive">true</boolProp>
          <boolProp name="HTTPSampler.DO_MULTIPART_POST">false</boolProp>
          <stringProp name="HTTPSampler.embedded_url_re"></stringProp>
          <stringProp name="HTTPSampler.connect_timeout"></stringProp>
          <stringProp name="HTTPSampler.response_timeout"></stringProp>
        </HTTPSamplerProxy>
        <hashTree>
          <HeaderManager guiclass="HeaderPanel" testclass="HeaderManager" testname="HTTP Header Manager" enabled="true">
            <collectionProp name="HeaderManager.headers">
              <elementProp name="" elementType="Header">
                <stringProp name="Header.name">Content-Type</stringProp>
                <stringProp name="Header.value">application/json</stringProp>
              </elementProp>
            </collectionProp>
          </HeaderManager>
          <hashTree/>
          </hashTree>
    """%data
  DATA.append(new_data)




def save(file_in='dfva_python/tests/jmeter_template.jmx', file_out='jmeter.jmx'):
    with open(file_in) as arch:
        tmp = arch.read()

    data = "".join(DATA)
    with open(file_out, 'w') as arch:
      arch.write(tmp%data)
