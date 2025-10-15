import nose
import sys
import os
from datetime import datetime


sys.path.append(os.path.abspath('../'))
result = nose.run('tests')




from dfva_python import jmeter_logger
jmeter_logger.save(file_out="jemeter_test_"+
    datetime.now().isoformat()+'.jmx',
                   file_in='tests/jmeter_template.jmx'
)