#!/usr/bin/env python
import os
import sys

sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir))

import settings
import web
import views
app = web.app

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=settings.CORE_PORT, debug=True)
