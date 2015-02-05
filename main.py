import os
import urllib
import json
import datetime
import time
import math

from google.appengine.api import users
from google.appengine.api import images
from google.appengine.ext import ndb
from google.appengine.api import mail
from google.appengine.api import urlfetch
from google.appengine.ext import blobstore
from google.appengine.ext.webapp import blobstore_handlers

import webapp2
import jinja2

UserEmail = ""

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

def lost_key():
    return ndb.Key('kind', 'lost')
def found_key():
    return ndb.Key('kind', 'found')
# define ndb model to store user info
class Email(ndb.Model):
	pw = ndb.StringProperty()

# define ndb model to store lost item info
class Lost(ndb.Model):
    order = ndb.DateTimeProperty(auto_now_add=True) 
    contact = ndb.StringProperty()
    image = ndb.StringProperty()
    date = ndb.StringProperty()  
    title = ndb.StringProperty()
    description = ndb.StringProperty()
    category = ndb.StringProperty()
    geo = ndb.JsonProperty()
    address = ndb.StringProperty()

# define ndb model to store found item info
class Found(ndb.Model):
    order = ndb.DateTimeProperty(auto_now_add=True) 
    contact = ndb.StringProperty()
    image = ndb.StringProperty()
    date = ndb.StringProperty()  
    title = ndb.StringProperty()
    description = ndb.StringProperty()
    category = ndb.StringProperty()
    geo = ndb.JsonProperty()
    address = ndb.StringProperty()

class MainPage(webapp2.RequestHandler):
    def get(self):
        global UserEmail
        if UserEmail != "":
            signInOut = "Sign Out"
            signUrl = '/signOut'
            myPost = 'My Posts'
            myUrl ='/manage'

        else: 
            signInOut = "Sign In"
            signUrl = '/signIn'
            myPost =''
            myUrl =''
        # fetch data from mainAPI
        params = {}
        fetchUrl = "http://aptlostfound.appspot.com/mainAPI"
        payload = json.dumps(params)
        result = urlfetch.fetch(fetchUrl, payload = payload, method = urlfetch.POST).content
        result = json.loads(result)
        template_values = {
        'signInOut':signInOut,
        'signUrl': signUrl,
        'result':result,
        'myPost':myPost,
        'myUrl':myUrl
        }
        template = JINJA_ENVIRONMENT.get_template('main.html')
        self.response.write(template.render(template_values))

class MainAPI(webapp2.RequestHandler):
    def post(self):
        result = {}
        lostInfo = []
        losts = Lost.query(ancestor=lost_key()).order(-Lost.order)
        losts = losts.fetch(5)
        for item in losts:
            info = {}
            info['email'] = item.contact
            info['title'] = item.title
            info['date'] = item.date
            info['desc'] = item.description
            info['img'] = item.image
            info['cate'] = item.category
            info['addr'] = item.address
            lostInfo.append(info)
        foundInfo = []
        founds = Found.query(ancestor=found_key()).order(-Found.order)
        founds = founds.fetch(5)
        for item in founds:
            info = {}
            info['email'] = item.contact
            info['title'] = item.title
            info['date'] = item.date
            info['desc'] = item.description
            info['img'] = item.image
            info['cate'] = item.category
            info['addr'] = item.address
            foundInfo.append(info)
        result['lost'] = lostInfo
        result['found'] = foundInfo
        self.response.write(json.dumps(result))

class ManagePage(webapp2.RequestHandler):
    def get(self):
        # fetch data from mainAPI
        params = {}
        fetchUrl = "http://aptlostfound.appspot.com/manageAPI"
        payload = json.dumps(params)
        result = urlfetch.fetch(fetchUrl, payload = payload, method = urlfetch.POST).content
        result = json.loads(result)
        print result
        delete = "http://aptlostfound.appspot.com/deleteAPI"
        template_values = {
        'result':result,
        'delete':delete
        }
        template = JINJA_ENVIRONMENT.get_template('manage.html')
        self.response.write(template.render(template_values))

class ManageAPI(webapp2.RequestHandler):
    def post(self):
        global UserEmail
        result = {}
        lostInfo = []
        losts = Lost.query(Lost.contact == UserEmail,ancestor=lost_key()).order(-Lost.order)
        for item in losts:
            info = {}
            info['key'] = item.key.urlsafe()
            info['title'] = item.title
            info['date'] = item.date
            info['desc'] = item.description
            info['img'] = item.image
            info['cate'] = item.category
            lostInfo.append(info)
        foundInfo = []
        founds = Found.query(Found.contact == UserEmail,ancestor=found_key()).order(-Found.order)
        for item in founds:
            info = {}
            info['key'] = item.key.urlsafe()
            info['title'] = item.title
            info['date'] = item.date
            info['desc'] = item.description
            info['img'] = item.image
            info['cate'] = item.category
            foundInfo.append(info)
        result['lost'] = lostInfo
        result['found'] = foundInfo
        self.response.write(json.dumps(result))

class DeleteAPI(webapp2.RequestHandler):
    def post(self):
        keys = self.request.get_all('delete')
        for key in keys:
            key = ndb.Key(urlsafe=key)
            key.delete()
        self.redirect('http://aptlostfound.appspot.com/manage?'+str(time.time()))

class SignInPage(webapp2.RequestHandler):
    def get(self):
        template_values = {}
        template = JINJA_ENVIRONMENT.get_template('signIn.html')
        self.response.write(template.render(template_values))

class SignInAPI(webapp2.RequestHandler):
    def post(self):
        global UserEmail
        email = self.request.get('email').lower()
        pw = self.request.get('pw')
        user = Email.get_by_id(email)
        result = {}
        if user == None:
            result["status"] = "fail"
            result["error"] = "The emali does not register"
        else :
            if user.pw == pw:
                result["status"] = "success"
                UserEmail = email
                print UserEmail
            else:
                result["status"] = "fail"
                result["error"] = "The password is wrong!"
        self.response.write(json.dumps(result))

class SignOutAPI(webapp2.RequestHandler):
    def get(self):
        global UserEmail
        UserEmail = ""
        self.redirect('http://aptlostfound.appspot.com')

class RegisterPage(webapp2.RequestHandler):
    def get(self):
        template_values = {}
        template = JINJA_ENVIRONMENT.get_template('register.html')
        self.response.write(template.render(template_values))

class RegisterAPI(webapp2.RequestHandler):
    def post(self):
        email = self.request.get('email').lower()
        pw = self.request.get('pw')
        user = Email()
        key = ndb.Key(Email,email)
        user.key = key
        user.pw = pw
        user.put()
        self.redirect('http://aptlostfound.appspot.com')

class Post(webapp2.RequestHandler):
    def get(self,kind):
        global UserEmail
        if UserEmail != "":
            myUrl ='/manage'
            myPost = 'My Posts'
            if kind == 'lost':
                date = 'Date item was lost:'
                loc = 'Location item was lost'
                url = '/upload/lost'
            else:
                date = 'Date item was found:'
                loc = 'Location item was found'
                url = '/upload/found'      
            upload_url = blobstore.create_upload_url(url)
            print upload_url
            template_values = {'action':upload_url,'date':date,'loc':loc,'myUrl':myUrl,'myPost':myPost}
            template = JINJA_ENVIRONMENT.get_template('report.html')
        else:
            myUrl =''
            myPost =''      
            template_values = {'myUrl':myUrl,'myPost':myPost}
            template = JINJA_ENVIRONMENT.get_template('error.html')
        self.response.write(template.render(template_values))

class BlobUrl(webapp2.RequestHandler):
    def get(self,kind):
        if kind == 'lost':
            url = '/upload/lost'
        else:
            url = '/upload/found'
        upload_url = blobstore.create_upload_url(url)
        result = {"url":upload_url}
        self.response.write(json.dumps(result))

class PostUploadAPI(blobstore_handlers.BlobstoreUploadHandler):
    def post(self,kind):
        global UserEmail
        # get image url
        upload_files = self.get_uploads('file')
        url = ''
        if len(upload_files) > 0:
            blob_info = upload_files[0]
            imageKey = blob_info.key()
            url = images.get_serving_url(imageKey,size=None,crop=False,secure_url=None)
        print "urlimg",url
        # get other info from form
        date = self.request.get('date')
        cate = self.request.get('category')
        title = self.request.get('title')
        desc = self.request.get('description')
        location = self.request.get('location')
        address = self.request.get('address')
        loc = location[1:-1].split(',')
        geo = {}
        geo['lat'] = float(loc[0])
        geo['lng'] = float(loc[1])
        if kind == 'lost':
            item = Lost(parent=lost_key())
        else: item = Found(parent=found_key())
        item.contact = UserEmail
        item.image = url
        item.date = date
        item.title = title
        item.description = desc
        item.category = cate
        item.address = address
        item.geo = json.dumps(geo)
        item.put()
        self.redirect('http://aptlostfound.appspot.com')

class SearchPage(webapp2.RequestHandler):
    def get(self,kind):
        global UserEmail
        if UserEmail != "":
            signInOut = "Sign Out"
            signUrl = '/signOut'
            myUrl ='/manage'
            myPost ='My Posts'
        else: 
            signInOut = "Sign In"
            signUrl = '/signIn'
            myUrl = ''
            myPost = ''
        if kind == 'lost':
            title = 'Lost'
            url = 'http://aptlostfound.appspot.com/searchAPI/lost'
        else:
            title = "Found"
            url = 'http://aptlostfound.appspot.com/searchAPI/found'
        template_values = {'title':title, 'url':url,'signInOut':signInOut,'signUrl':signUrl,'myUrl':myUrl,'myPost':myPost}
        template = JINJA_ENVIRONMENT.get_template('search.html')
        self.response.write(template.render(template_values))

class SearchAPI(webapp2.RequestHandler):
    def post(self,kind):
        keyword = self.request.get('keyword')
        cate = self.request.get('cate')
        if kind == 'lost':
            items = Lost.query(ndb.OR(Lost.category == cate, Lost.title == keyword))
        else:
            items = Found.query(ndb.OR(Lost.category == cate, Lost.title == keyword))            
        result = []
        for item in items:
            info = {}
            info['email'] = item.contact
            info['title'] = item.title
            info['date'] = item.date
            info['desc'] = item.description
            info['img'] = item.image
            info['cate'] = item.category
            info['addr'] = item.address
            result.append(info)
        self.response.write(json.dumps(result))

class NearbyAPI(webapp2.RequestHandler):
    def getDistance(self,la1, lo1, la2, lo2):
        la1 = float(la1)
        lo1 = float(lo1)
        la2 = float(la2)
        lo2 = float(lo2)
        print la1, lo1, la2, lo2
        R = 6371.0
        la1_radian = math.radians(la1)
        la2_radian = math.radians(la2)
        delta_la = math.radians(la2-la1)
        delta_lo = math.radians(lo2-lo1)
        a = math.pow(math.sin(delta_la/2), 2) + math.cos(la1_radian)*math.cos(la2_radian)*math.pow(math.sin(delta_lo/2), 2)
        print a
        c = 2* math.atan2(math.sqrt(a), math.sqrt(1-a))
        return R*c

    def get(self):
        la1 = self.request.get('latitude')
        lo1 = self.request.get('longitude')
        result = {}
        lostInfo = []
        losts = Lost.query()
        for item in losts:
            title = item.title
            date = item.date
            desc = item.description
            img = item.image
            cate = item.category
            address = item.address
            geo = json.loads(item.geo)
            la2 = geo['lat']
            lo2 = geo['lng']
            distance = self.getDistance(la1, lo1, la2, lo2)
            lostInfo.append([str(distance),title,date,desc,img,cate,address])
            lostInfo = sorted(lostInfo, key=lambda x:float(x[0]))
        foundInfo = []
        founds = Found.query()
        for item in founds:
            title = item.title
            date = item.date
            desc = item.description
            img = item.image
            cate = item.category
            address = item.address
            geo = json.loads(item.geo)
            la2 = geo['lat']
            lo2 = geo['lng']
            distance = self.getDistance(la1, lo1, la2, lo2)
            foundInfo.append([str(distance),title,date,desc,img,cate,address])
            foundInfo = sorted(foundInfo, key=lambda x:float(x[0]))
        result['lost'] = lostInfo
        result['found'] = foundInfo
        self.response.write(json.dumps(result))

class Test(webapp2.RequestHandler):
    def get(self):
        # items = Found.query()
        # for item in items:
        #     print item.title
        #     print item.contact
        #     print item.image
        #     print item.date
        #     print item.description
        #     print item.category
        #     print item.geo
        template_values = {}
        template = JINJA_ENVIRONMENT.get_template('test.html')
        self.response.write(template.render(template_values))



app = webapp2.WSGIApplication([
	('/test',Test),
    ('/', MainPage), ('/mainAPI',MainAPI),
    ('/signIn', SignInPage), ('/signInAPI', SignInAPI),
    ('/signOut', SignOutAPI),
    ('/manage',ManagePage),('/manageAPI',ManageAPI),('/deleteAPI',DeleteAPI),
    ('/register', RegisterPage),('/registerAPI', RegisterAPI),
    ('/post/([^/]+)?', Post),
    ('/blobUrl/([^/]+)?', BlobUrl),('/upload/([^/]+)?', PostUploadAPI),
    ('/search/([^/]+)?',SearchPage),('/searchAPI/([^/]+)?',SearchAPI),
    ('/nearbyAPI',NearbyAPI)
], debug=True)
