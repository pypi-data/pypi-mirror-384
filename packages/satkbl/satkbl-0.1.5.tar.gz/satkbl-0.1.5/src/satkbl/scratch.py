# for testing

import satkbl.util as u
import satkbl.req as req
import satkbl.ctx as ctx

c = ctx.generic('http://example.com')
r = req.geth(c, '')
u.lrd(r)
