#!/usr/bin/env python
# -*- coding: ISO-8859-1 -*-
#  OKUSON Package
#  Frank L�beck and Max Neunh�ffer

'''This is the place where all special web services are implemented.'''

CVS = '$Id: WebWorkers.py,v 1.75 2004/03/02 15:32:23 neunhoef Exp $'

import os,sys,time,locale,traceback,random,crypt,string,Cookie,signal,cStringIO

import Config,Data,Exercises

from fmTools import BuiltinWebServer, XMLRewrite, Utils, AsciiData
from fmTools import SimpleTemplate, LatexImage

def LocalTimeString(t = None):
  if t == None: t = time.time()
  return time.strftime("%c", time.localtime(t))

LETTERS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"

# First we set our document root:
DocRoot = BuiltinWebServer.DocRoot = Config.conf['DocumentRoot']
ElHandlers = XMLRewrite.ElementHandlers_tpl
# We store an xml header with DOCTYPE for XHTML 1.0 Strict into the
# class variable "begin" such that this is the global default header:
XMLRewrite.PreparsedXMLWebResponse.begin = \
'''<?xml version="1.0" encoding="ISO-8859-1"?>

<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"
                      "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">

'''

ValidatorIconText = '''<a href="http://validator.w3.org/check/referer">
<img src="/images/valid-xhtml10.png" alt="Valid XHTML 1.0!" 
     height="31" width="88" /></a>
'''
# Make the main site dictionary available here:

Site = BuiltinWebServer.Site

# The following is a random integer, once the administrator is logged in:
currentcookie = None

# Helper for installing dynamic pages:
# There are two different sorts of pages:
# 1) Pages without input which are generated from templates by filling
#    in some values.
# 2) Pages with input that trigger a function that works on the input
#    and sends out a page of the first kind.
PPXML = XMLRewrite.PreparsedXMLWebResponse
FunWR = BuiltinWebServer.FunctionWebResponse

# This allows access to the Site dictionary, see at the end of the file
# for the corresponding release statement:
BuiltinWebServer.SiteLock.acquire()

#############################################################################
#
# Generic element handlers:
#
# We inherit from XMLRewrite.XMLElementHandlers and add a few element
# handlers that are used throughout all our dynamic pages:
#
class EH_Generic_class(XMLRewrite.XMLElementHandlers):
    iamadmin = 0
    def handle_CourseName(self,node,out):
        out.write(Config.conf['CourseName'])
    def handle_Semester(self,node,out):
        out.write(Config.conf['Semester'])
    def handle_Lecturer(self,node,out):
        out.write(Config.conf['Lecturer'])
    def handle_User1(self,node,out):
        if Config.conf.has_key('User1'):
            out.write(Config.conf['User1'])
    def handle_User2(self,node,out):
        if Config.conf.has_key('User2'):
            out.write(Config.conf['User2'])
    def handle_User3(self,node,out):
        if Config.conf.has_key('User3'):
            out.write(Config.conf['User3'])
    def handle_User4(self,node,out):
        if Config.conf.has_key('User4'):
            out.write(Config.conf['User4'])
    def handle_User5(self,node,out):
        if Config.conf.has_key('User5'):
            out.write(Config.conf['User5'])
    def handle_User6(self,node,out):
        if Config.conf.has_key('User6'):
            out.write(Config.conf['User6'])
    def handle_User7(self,node,out):
        if Config.conf.has_key('User7'):
            out.write(Config.conf['User7'])
    def handle_User8(self,node,out):
        if Config.conf.has_key('User8'):
            out.write(Config.conf['User8'])
    def handle_User9(self,node,out):
        if Config.conf.has_key('User9'):
            out.write(Config.conf['User9'])
    def handle_Feedback(self,node,out):
        out.write(Config.conf['Feedback']+'\n')
    def handle_PossibleStudies(self,node,out):
        for opt in Config.conf['PossibleStudies']:
            out.write('  <option>'+opt+'</option>\n')
    def handle_CurrentTime(self,node,out):
        out.write(LocalTimeString())
    def handle_ValidatorIcon(self,node,out):
        out.write(ValidatorIconText)
    def handle_GroupSize(self,node,out):
        if node[1] == None or not(node[1].has_key('number')):
            Utils.Error('Found <GroupSize /> tag without "number" attribute. '
                        'Ignoring.',prefix='Warning: ') 
            return
        try:
            nr = node[1]['number'].encode('ISO-8859-1','replace')
        except:
            Utils.Error('Found "number" attribute in <GroupSize /> tag with '
                        'value not being a non-negative integer. Ignoring.',
                        prefix='Warning: ')
            return
        if Data.groups.has_key(nr):
            out.write(str(len(Data.groups[nr].people)))
        else:
            out.write('0')
    def handle_GroupDistribution(self,node,out):
        l = Utils.SortNumerAlpha(Data.people.keys())
        for k in l:
            if not(Config.conf['GuestIdRegExp'].match(k)):
                out.write('<tr><td>'+k+'</td><td>'+str(Data.people[k].group)+
                          '</td></tr>\n')
    def handle_GroupsOverview(self,node,out):
        l = Utils.SortNumerAlpha(Data.groups.keys())
        try:
            fields = node[1]['components'].encode('ISO-8859-1','replace')
            fields = map(lambda s: s.strip(), string.split(fields,','))
        except:
            # default
            fields = ['number', 'place', 'tutor', 'nrparticipants']
            
        s = []
        for nr in l:
            grp = Data.groups[nr]
            grp.nrparticipants = len(grp.people)
            s.append('<tr>')
            for a in fields:
                if hasattr(grp, a):
                    if a in ['number','nrparticipants']:
                        s.append('<td><a href="/GroupInfo?number='+str(nr)+'">'+
                             str(getattr(grp, a))+'</a></td>')
                    else:
                        s.append('<td>'+str(getattr(grp, a))+'</td>')
            s.append('</tr>\n')
        out.write(string.join(s,''))
    def handle_MembersOfGroup(self,node,out):
        if node[1] == None or not(node[1].has_key('number')):
            Utils.Error('Found <MemberOfGroups /> tag without "number" '
                        'attribute. Ignoring.',prefix='Warning: ') 
            return
        try:
            nr = int(node[1]['number'])
        except:
            Utils.Error('Found "number" attribute in <MembersOfGroup /> tag '
                        'with value not being a non-negative integer. '
                        'Ignoring.', prefix='Warning: ')
            return
        if Data.groups.has_key(nr):
            l = Utils.SortNumerAlpha(Data.groups[nr].people)
            out.write(string.join(l,', ')+'.')
        else:
            Utils.Error('<MembersOfGroup /> tag requested empty group "'+
                        str(nr)+'".',prefix='Warning: ')
    def handle_LoginStatus(self,node,out):
        if currentcookie != None:
            out.write('There is somebody logged in. '
                      '<a href="/AdminLogout">Logout</a>\n')
        else:
            out.write('Nobody logged in. Please enter administrator password '
                      'next to the button you use or '
                      '<a href="/adminlogin.html">login here.</a>\n')
    def handle_ServerStatus(self,node,out):
        if currentcookie != None:
            out.write('There is somebody logged in. ')
        else:
            out.write('Nobody logged in. ')
    def handle_AdminPasswdField(self,node,out):
        if currentcookie == None:
            out.write('<input type="password" size="16" maxlength="16" '
                      'name="passwd" value="" />\n')
    def handle_AvailableSheetsAsButtons(self,node,out):
       l = Exercises.SheetList()
       for nr,name,s in l:
           if len(name) == 1:
             name = ' '+name
           if s.openfrom and time.time() < s.openfrom:
               if self.iamadmin:
                   out.write('(<input type="submit" name="sheet" value="'
                      +name+'" tabindex="'+str(1000-nr)+'"/> not yet open)\n')
           else:
               out.write('<input type="submit" name="sheet" value="'
                         +name+'" tabindex="'+str(1000-nr)+'"/>\n')
    def handle_AvailableResolutions(self,node,out):
        out.write('<option selected="selected">Standard</option>\n')
        for r in Config.conf['Resolutions']:
            out.write('<option>'+str(r)+'</option>\n')    
    def handle_AvailableIds(self,node,out):
        if currentcookie == None:
            out.write('<input size="8" maxlength="6" name="msgid" value="" '
                      '/>\n')
        else:
            out.write('<select name="msgid">\n')
            l = Utils.SortNumerAlpha(Data.people.keys())
            for k in l:
               if not(Config.conf['GuestIdRegExp'].match(k)):
                   p = Data.people[k]
                   out.write('<option value="'+k+'">'+k+' - '+p.fname+' '
                             +p.lname+'</option>\n')
            out.write('</select>\n')
            


EH_Generic = EH_Generic_class()

#
# Some helper functions:
#
def CleanQuotes(st):
    return st.replace('"','')

def Delegate(path,req,onlyhead,handler = None,addheader = []):
    '''This delegates to another path.'''
    if handler == None:
        (header,response) = Site[path].getresult(req,onlyhead)
    else:
        (header,response) = Site[path].getresult(req,onlyhead,handler)
    header['Content-Location'] = path
    for k,v in addheader: header[k] = v
    return (header,response)

def Authenticate(p,req,onlyhead):
    '''Checks password in the request. Administrator password is also 
       accepted. Return value is 1 if authentication was with admin
       password or login (documented by cookie) and 0 otherwise. In case
       of a failure we return -1.'''
    global currentcookie
    if p != None:    # We use p == None for a check for administrator
        # Check whether password is correct:
        pw = req.query.get('passwd',['1'])[0].strip()[:16]
        salt = p.passwd[:2]
        passwd = crypt.crypt(pw,salt)
        # First authenticate regular users with their password:
        if passwd == p.passwd:
            return 0
    # Check for cookie:
    cookie = Cookie.SimpleCookie()
    cookie.load('Cookie: '+req.headers.get('Cookie',''))
    try: 
        cookieval = cookie['OKUSON'].value
    except:
        cookieval = ''
    # Check admin password:
    passwdadmin = crypt.crypt(pw,Config.conf['AdministratorPassword'][:2])
    if (cookieval == currentcookie or \
        passwdadmin == Config.conf['AdministratorPassword']) and \
       BuiltinWebServer.check_address(Config.conf['AdministrationAccessList'],
                                      req.client_address[0]):
        return 1     # Administrator
    if not(Config.conf['GuestIdRegExp'].match(p.id)):
        return -1    # Failure
    else:
        return 0     # Guest authentication


def AuthenticateTutor(g,req,onlyhead):
    '''Checks password in the request. Administrator password is also 
       accepted. Return value is 1 if authentication was with admin
       password and 0 otherwise. In case of a failure we return -1.'''
    # Check whether password is correct:
    pw = req.query.get('passwd',['1'])[0].strip()[:16]
    salt = g.passwd[:2]
    passwd = crypt.crypt(pw,salt)
    # Check admin password:
    passwdadmin = crypt.crypt(pw,Config.conf['AdministratorPassword'][:2])
    if passwdadmin == Config.conf['AdministratorPassword'] and \
       BuiltinWebServer.check_address(Config.conf['AdministrationAccessList'],
                                      req.client_address[0]):
        iamadmin = 1
    else:
        iamadmin = 0
    if passwd != g.passwd and not(iamadmin):
        return -1
    else:
        return iamadmin

def SubmitRegistration(req,onlyhead):
    '''This function is called when a user submits a registration. It will
work on the submitted form data, register the new participant if possible
and either send an error message or a report.'''
    # First check whether the id is valid:
    id = req.query.get('id',[''])[0].strip()   # our default id
    if not(Config.conf['IdCheckRegExp'].match(id)):
        return Delegate('/errors/invalidid.html',req,onlyhead)

    # Now check whether the two passwords are identical:
    pw1 = req.query.get('passwd',['1'])[0].strip()[:16]
    pw2 = req.query.get('passwd2',['2'])[0].strip()[:16]
    if pw1 != pw2:
        return Delegate('/errors/diffpasswd.html',req,onlyhead)

    # Now check for empty fields:
    lname = req.query.get('lname',[''])[0].strip()[:30]
    fname = req.query.get('fname',[''])[0].strip()[:30]
    stud = req.query.get('stud',[''])[0].strip()[:30]
    topic = req.query.get('topic',[''])[0].strip()[:30]
    if topic != '': stud = topic
    sem = req.query.get('sem',[''])[0].strip()[:2]
    try:
        sem = int(sem)
    except:
        sem = 0
    if sem <= 0:
        return Delegate('/errors/semnonumber.html',req,onlyhead)

    if lname == '' or fname == '' or stud == '':
        return Delegate('/errors/emptyfields.html',req,onlyhead)

    email = req.query.get('email',[''])[0].strip()[:80]
    wishes = req.query.get('wishes',[''])[0].strip()[:80]

    # additional, not further specified, personal data for customization
    # (each can store up to 256 characters)
    persondata1 = req.query.get('persondata1',[''])[0].strip()[:256]
    persondata2 = req.query.get('persondata2',[''])[0].strip()[:256]
    persondata3 = req.query.get('persondata3',[''])[0].strip()[:256]
    persondata4 = req.query.get('persondata4',[''])[0].strip()[:256]
    persondata5 = req.query.get('persondata5',[''])[0].strip()[:256]
    persondata6 = req.query.get('persondata6',[''])[0].strip()[:256]
    persondata7 = req.query.get('persondata7',[''])[0].strip()[:256]
    persondata8 = req.query.get('persondata8',[''])[0].strip()[:256]
    persondata9 = req.query.get('persondata9',[''])[0].strip()[:256]

    # Construct data line with encrypted password:
    salt = random.choice(LETTERS) + random.choice(LETTERS)
    passwd = crypt.crypt(pw1,salt)
    line = AsciiData.LineTuple( (id,lname,fname,str(sem),stud,passwd,email,
                                 wishes,
                                 persondata1, persondata2, persondata3,
                                 persondata4, persondata5, persondata6,
                                 persondata7, persondata8, persondata9 ) )

    # Create a new Person object:
    p = Data.Person()
    p.id = id
    p.lname = lname
    p.fname = fname
    p.sem = sem
    p.stud = stud
    p.passwd = passwd
    p.email = email
    p.wishes = wishes
    p.persondata1 = persondata1
    p.persondata2 = persondata2
    p.persondata3 = persondata3
    p.persondata4 = persondata4
    p.persondata5 = persondata5
    p.persondata6 = persondata6
    p.persondata7 = persondata7
    p.persondata8 = persondata8
    p.persondata9 = persondata9

    # Then check at last whether we already have someone with that id:
    Data.Lock.acquire()
    if Data.people.has_key(id):
        Data.Lock.release()
        return Delegate('/errors/idinuse.html',req,onlyhead)
        
    # Put new person into file on disk:
    try:
        Data.peopledesc.AppendLine(line)
    except:
        Data.Lock.release()
        Utils.Error('Failed to register person:\n'+line)
        return Delegate('/errors/fatal.html',req,onlyhead)
    
    # Put new person into database in memory:
    Data.people[id] = p
    Data.AddToGroupStatistic(p)
    Data.Lock.release()

    # At last write out a sensible response:
    Utils.Error('registered '+id, prefix='SubmitRegistration: ')
    return Delegate('/messages/regsuccess.html',req,onlyhead)

Site['/SubmitRegistration'] = FunWR(SubmitRegistration)

class EH_withPersData_class(EH_Generic_class):
    '''This class exists to produce handlers that can fill in personal data
into a web sheet. It has some additional non-generic methods and holds
one Person object as data.'''
    p = None    # here we store the concrete personal data
    def __init__(self,p):
        self.p = p
    def handle_IdOfPerson(self,node,out):
        out.write(str(self.p.id))
    def handle_HiddenIdField(self,node,out):
        out.write('<input type="hidden" name="id" value="'+
                  CleanQuotes(self.p.id)+'" />'+self.p.id)
    def handle_LastName(self,node,out):
        out.write(str(self.p.lname))
    def handle_LastNameField(self,node,out):
        out.write('<input size="30" maxlength="30" name="lname" value="'+
                  CleanQuotes(self.p.lname)+'" />')
    def handle_FirstName(self,node,out):
        out.write(str(self.p.fname))
    def handle_FirstNameField(self,node,out):
        out.write('<input size="30" maxlength="30" name="fname" value="'+
                  CleanQuotes(self.p.fname)+'" />')
    def handle_PersonData1Field(self,node,out):
        out.write('<input size="30" maxlength="256" name="persondata1" ' + \
                  'value="'+ CleanQuotes(self.p.persondata1)+'" />')
    def handle_PersonData2Field(self,node,out):
        out.write('<input size="30" maxlength="256" name="persondata2" ' + \
                  'value="'+ CleanQuotes(self.p.persondata2)+'" />')
    def handle_PersonData3Field(self,node,out):
        out.write('<input size="30" maxlength="256" name="persondata3" ' + \
                  'value="'+ CleanQuotes(self.p.persondata3)+'" />')
    def handle_PersonData4Field(self,node,out):
        out.write('<input size="30" maxlength="256" name="persondata4" ' + \
                  'value="'+ CleanQuotes(self.p.persondata4)+'" />')
    def handle_PersonData5Field(self,node,out):
        out.write('<input size="30" maxlength="256" name="persondata5" ' + \
                  'value="'+ CleanQuotes(self.p.persondata5)+'" />')
    def handle_PersonData6Field(self,node,out):
        out.write('<input size="30" maxlength="256" name="persondata6" ' + \
                  'value="'+ CleanQuotes(self.p.persondata6)+'" />')
    def handle_PersonData7Field(self,node,out):
        out.write('<input size="30" maxlength="256" name="persondata7" ' + \
                  'value="'+ CleanQuotes(self.p.persondata7)+'" />')
    def handle_PersonData8Field(self,node,out):
        out.write('<input size="30" maxlength="256" name="persondata8" ' + \
                  'value="'+ CleanQuotes(self.p.persondata8)+'" />')
    def handle_PersonData9Field(self,node,out):
        out.write('<input size="30" maxlength="256" name="persondata9" ' + \
                  'value="'+ CleanQuotes(self.p.persondata9)+'" />')
    def handle_PersonData1(self, node, out):
        out.write(self.p.persondata1)
    def handle_PersonData2(self, node, out):
        out.write(self.p.persondata2)
    def handle_PersonData3(self, node, out):
        out.write(self.p.persondata3)
    def handle_PersonData4(self, node, out):
        out.write(self.p.persondata4)
    def handle_PersonData5(self, node, out):
        out.write(self.p.persondata5)
    def handle_PersonData6(self, node, out):
        out.write(self.p.persondata6)
    def handle_PersonData7(self, node, out):
        out.write(self.p.persondata7)
    def handle_PersonData8(self, node, out):
        out.write(self.p.persondata8)
    def handle_PersonData9(self, node, out):
        out.write(self.p.persondata9)
    def handle_PersonDataRadioButton(self, node, out):
        try:
            name = node[1]['name'].encode('ISO-8859-1','replace')
            val = node[1]['value'].encode('ISO-8859-1','replace')
            known = str(getattr(self.p, name))
        except:
            return
        res = ['<input type="radio" name="', name, '" value="', val, '" '] 
        if val == known:
            res.append('checked="checked" ')
        res.append('/>')
        out.write(string.join(res, ''));
    def handle_PersonDataCheckBox(self, node, out):
        try:
            name = node[1]['name'].encode('ISO-8859-1','replace')
            val = node[1]['value'].encode('ISO-8859-1','replace')
            known = str(getattr(self.p, name))
        except:
            return
        res = ['<input type="checkbox" name="', name, '" value="', val, '" '] 
        if val == known:
            res.append('checked="checked" ')
        res.append('/>')
        out.write(string.join(res, ''));
    def handle_PersonDataSelectOption(self, node, out):
        try:
            name = node[1]['name'].encode('ISO-8859-1','replace')
            val = node[1]['value'].encode('ISO-8859-1','replace')
            known = str(getattr(self.p, name))
            if node[1].has_key('content'):
                cont = node[1]['content'].encode('ISO-8859-1','replace')
            else:
                cont = val
        except:
            return
        res = ['<option value="'+val+'" '] 
        if val == known:
            res.append(' selected="selected" ')
        res.append('>'+cont+'</option>\n')
        out.write(string.join(res, ''));
    def handle_PossibleStudies(self,node,out):
        found = 0
        for i in range(len(Config.conf['PossibleStudies'])):
            opt = Config.conf['PossibleStudies'][i]
            if (self.p.stud == opt) or \
               (found == 0 and i == len(Config.conf['PossibleStudies'])-1):
                out.write('  <option selected="selected">'+opt+'</option>\n')
                found = 1
            else:
                out.write('  <option>'+opt+'</option>\n')
    def handle_Topic(self,node,out):
        out.write(str(self.p.stud))
    def handle_TopicField(self,node,out):
        out.write('<input size="18" maxlength="30" name="topic" value="')
        if not(self.p.stud in Config.conf['PossibleStudies']):
            out.write(self.p.stud)
        out.write('" />')
    def handle_Sem(self,node,out):
        out.write(str(self.p.sem))
    def handle_SemesterField(self,node,out):
        out.write('<input size="2" maxlength="2" name="sem" value="'+
                  str(self.p.sem)+'" />')
    def handle_Email(self,node,out):
        out.write(str(self.p.email))
    def handle_EmailField(self,node,out):
        out.write('<input size="30" maxlength="80" name="email" value="'+
                  CleanQuotes(self.p.email)+'" />')
    def handle_Wishes(self,node,out):
        out.write(str(self.p.wishes))
    def handle_WishesField(self,node,out):
        out.write('<input size="30" maxlength="80" name="wishes" value="'+
                  CleanQuotes(self.p.wishes)+'" />')
    def handle_Results(self,node,out):
        # Check attributes if interactive and/or homework exercises are
        # considered (not given attributes mean 'true').
        try:
            fields = node[1]['components'].encode('ISO-8859-1','replace')
            fields = map(lambda s: s.strip(), string.split(fields,','))
        except:
            # the default
            fields = ['interactive', 'homework']
        l = Exercises.SheetList()
        for nr,name,s in l:
            if s.IsClosed():   # sheet already closed 
                if self.p.mcresults.has_key(name):
                    mcscore = str(self.p.mcresults[name].score)
                else:
                    mcscore = '---'
                if 'withMaxMCScore' in fields:
                    mcscore += ' (' + str(s.MaxMCScore()) + ')'
                if self.p.homework.has_key(name):
                    homescore = str(self.p.homework[name].totalscore)
                else:
                    homescore = '?'
                if 'withMaxHomeScore' in fields:
                    if s.maxhomescore != -1:
                        homescore += ' (' + str(s.maxhomescore) + ')'
                    else:
                        homescore += ' (?)'
                out.write('<tr><td align="center">'+name+'</td>')
                if 'interactive' in fields:
                    out.write('<td align="center">'+mcscore+'</td>')
                if 'homework' in fields:
                    out.write('<td align="center">'+homescore+'</td>')
                out.write('</tr>\n')  
    def TotalMCScore(self):
        l = Exercises.SheetList()
        totalscore = 0
        for nr,name,s in l:
            if s.counts and s.IsClosed():   # sheet already closed 
                if self.p.mcresults.has_key(name):
                    totalscore += self.p.mcresults[name].score
        return totalscore
    def TotalHomeScore(self):
        l = Exercises.SheetList()
        totalscore = 0
        for nr,name,s in l:
            if s.counts and s.IsClosed():   # sheet already closed 
                if self.p.homework.has_key(name):
                    totalscore += self.p.homework[name].totalscore
        return totalscore
    def handle_TotalMCScore(self,node,out):
        out.write(str(self.TotalMCScore()))
    def handle_TotalHomeScore(self,node,out):
        out.write(str(self.TotalHomeScore()))
    def handle_TotalScore(self,node,out):
        out.write(str(self.TotalMCScore() + self.TotalHomeScore()))
    def MaxTotalMCScore(self):
        l = Exercises.SheetList()
        maxtotalmcscore = 0
        for nr,name,s in l:
            if s.counts and s.IsClosed():   # sheet already closed 
                maxtotalmcscore += s.MaxMCScore()
        return maxtotalmcscore
    def MaxTotalHomeScore(self):
        l = Exercises.SheetList()
        maxtotalhomescore = 0
        for nr,name,s in l:
            if s.counts and s.IsClosed():   # sheet already closed 
                if s.maxhomescore == -1:
                    maxtotalhomescore = -1
                if maxtotalhomescore != -1:
                    maxtotalhomescore += s.maxhomescore
        return maxtotalhomescore
    def handle_MaxTotalMCScore(self,node,out):
        out.write(str(self.MaxTotalMCScore()))
    def handle_MaxTotalHomeScore(self,node,out):
        maxtotalhomescore = self.MaxTotalHomeScore()
        if maxtotalhomescore != -1:
            out.write(str(maxtotalhomescore))
        else:
            out.write('?')
    def handle_MaxTotalScore(self,node,out):
        maxtotalmcscore = self.MaxTotalMCScore()
        maxtotalhomescore = self.MaxTotalHomeScore()
        if maxtotalhomescore != -1:
            out.write(str(maxtotalmcscore + maxtotalhomescore))
        else:
            out.write(str(maxtotalmcscore) + ' + ?')
    def handle_ExamGrades(self,node,out):
        if Config.conf['ExamGradingActive'] == 0 or \
           Config.conf['ExamGradingFunction'] == None: return
        for i in range(len(self.p.exams)):
            if self.p.exams[i] != None and self.p.exams[i].totalscore >= 0:
                try:
                    (msg,grade) = Config.conf['ExamGradingFunction'](self.p,i)
                    out.write('<p>\n'+msg+'</p>\n')
                except:
                    etype, value, tb = sys.exc_info()
                    lines = traceback.format_exception(etype,value,tb)
                    Utils.Error('Call of ExamGradingFunction raised an '
                            'exception, ID: '+self.p.id+', message:\n'+
                            string.join(lines))
    def handle_ExamGrade(self,node,out):
        if Config.conf['ExamGradingActive'] == 0 or \
           Config.conf['ExamGradingFunction'] == None: return
        if node[1] == None or not(node[1].has_key('nr')):
            return
        nr = node[1]['nr'].encode('ISO-8859-1','replace')
        try:
            nr = int(nr)
        except:
            Utils.Error('nr attribute value is no number: '+nr+' - assuming 0.')
            nr = 0
        if nr < 0 or nr >= len(self.p.exams): return
        try:
            (msg,grade) = Config.conf['ExamGradingFunction'](self.p,nr)
            out.write('<p>\n'+msg+'</p>\n')
        except:
            etype, value, tb = sys.exc_info()
            lines = traceback.format_exception(etype,value,tb)
            Utils.Error('Call of ExamGradingFunction raised an '
                    'exception, ID: '+self.p.id+', message:\n'+
                    string.join(lines))
    def handle_Grade(self,node,out):
        if Config.conf['GradingActive'] == 0 or \
           Config.conf['GradingFunction'] == None: return
        sl = Exercises.SheetList()
        homescore = mcscore = 0
        for nr,na,s in sl:
            if s.counts and s.IsClosed():   # we count it
                if self.p.mcresults.has_key(na):
                    mcscore += self.p.mcresults[na].score
                if self.p.homework.has_key(na):
                    homescore += self.p.homework[na].totalscore
        exams = []
        for i in range(24):
            if i >= len(self.p.exams) or self.p.exams[i] == None:
                exams.append(0)
            else:
                exams.append(self.p.exams[i].totalscore)
        try:
            (msg,grade) = Config.conf['GradingFunction']  \
                           (self.p,sl,mcscore,homescore,exams)
            out.write('<p>\n'+msg+'</p>\n')
        except:
            etype, value, tb = sys.exc_info()
            lines = traceback.format_exception(etype,value,tb)
            Utils.Error('Call of GradingFunction raised an exception, '
                        'ID: '+self.p.id+', message:\n'+string.join(lines))
    def handle_GeneralMessages(self,node,out):
        out.write(Config.conf['GeneralMessages'])
    def handle_PrivateMessages(self,node,out):
        for m in self.p.messages:
            out.write('<p>\n')
            out.write(m+'\n')
            out.write('</p>\n')
    def handle_PrivateMessagesForDeletion(self,node,out):
        '''This is called from the administrator's menu after he has
           requested to see the messages of one participant to delete
           some of those messages.'''
        out.write('<p><input type="hidden" name="id" value="'+self.p.id+
                  '" /></p>\n')
        for i in range(len(self.p.messages)):
            m = self.p.messages[i]
            out.write('<p><input type="checkbox" name="msg'+str(i)+
                      '" value="+" />'+m+'</p>\n')

def QueryRegChange(req,onlyhead):
    '''This function is called when a user asks to change his registration. 
It will work on the submitted form data, check whether a registration is
there and send a form to display and change the saved data.'''
    # First check whether the id is valid:
    id = req.query.get('id',[''])[0].strip()   # our default id
    if not(Config.conf['IdCheckRegExp'].match(id)):
        return Delegate('/errors/invalidid.html',req,onlyhead)

    # Then check whether we already have someone with that id:
    if not(Data.people.has_key(id)):
        return Delegate('/errors/idunknown.html',req,onlyhead)
        
    p = Data.people[id]
    iamadmin = Authenticate(p,req,onlyhead)
    if iamadmin < 0:
        return Delegate('/errors/wrongpasswd.html',req,onlyhead)

    currentHandler = EH_withPersData_class(p)
    return Delegate('/regchange2.html',req,onlyhead,currentHandler)

Site['/QueryRegChange'] = FunWR(QueryRegChange)

def SubmitRegChange(req,onlyhead):
    '''This function is called when a user submits a registration. It will
work on the submitted form data, register the new participant if possible
and either send an error message or a report.'''
    # First check whether the id is valid:
    id = req.query.get('id',[''])[0].strip()   # our default id
    if not(Config.conf['IdCheckRegExp'].match(id)):
        return Delegate('/errors/invalidid.html',req,onlyhead)

    # Then check whether we already have someone with that id:
    if not(Data.people.has_key(id)):
        return Delegate('/errors/idunknown.html',req,onlyhead)
        
    p = Data.people[id]
    iamadmin = Authenticate(p,req,onlyhead)
    if iamadmin < 0:
        return Delegate('/errors/wrongpasswd.html',req,onlyhead)

    # Now check whether the two new passwords are identical:
    pw1 = req.query.get('pw1',[''])[0].strip()[:16]
    pw2 = req.query.get('pw2',[''])[0].strip()[:16]
    if pw1 != '' or pw2 != '':
        if pw1 != pw2:
            return Delegate('/errors/diffpasswd.html',req,onlyhead)
        salt = random.choice(string.letters) + random.choice(string.letters)
        passwd = crypt.crypt(pw1,salt)
    else:   # here we have to set passwd correctly
        passwd = p.passwd

    # Now check for empty fields:
    lname = req.query.get('lname',[''])[0].strip()[:30]
    fname = req.query.get('fname',[''])[0].strip()[:30]
    stud = req.query.get('stud',[''])[0].strip()[:30]
    topic = req.query.get('topic',[''])[0].strip()[:30]
    if topic != '': stud = topic
    sem = req.query.get('sem',[''])[0].strip()[:2]
    try:
        sem = int(sem)
    except:
        sem = 0
    if sem <= 0:
        return Delegate('/errors/semnonumber.html',req,onlyhead)

    if lname == '' or fname == '' or stud == '':
        return Delegate('/errors/emptyfields.html',req,onlyhead)

    email = req.query.get('email',[''])[0].strip()[:80]
    wishes = req.query.get('wishes',[''])[0].strip()[:80]

    # additional, not further specified, personal data for customization
    # (each can store up to 256 characters)
    persondata1 = req.query.get('persondata1',[''])[0].strip()[:256]
    persondata2 = req.query.get('persondata2',[''])[0].strip()[:256]
    persondata3 = req.query.get('persondata3',[''])[0].strip()[:256]
    persondata4 = req.query.get('persondata4',[''])[0].strip()[:256]
    persondata5 = req.query.get('persondata5',[''])[0].strip()[:256]
    persondata6 = req.query.get('persondata6',[''])[0].strip()[:256]
    persondata7 = req.query.get('persondata7',[''])[0].strip()[:256]
    persondata8 = req.query.get('persondata8',[''])[0].strip()[:256]
    persondata9 = req.query.get('persondata9',[''])[0].strip()[:256]

    # Put person into file on disk:
    line = AsciiData.LineTuple( (id,lname,fname,str(sem),stud,passwd,email,
                                 wishes,
                                 persondata1, persondata2, persondata3,
                                 persondata4, persondata5, persondata6,
                                 persondata7, persondata8, persondata9 ) )

    # Note: Between the moment we looked up our person and stored it in
    # 'p' there might have been some change in the database, because we
    # acquire the lock only now. We carry on regardless, assuming that
    # we, being "later", have the latest data. Also, we only overwrite
    # fields in the very same "Person" object and so do not change other
    # data.
    Data.Lock.acquire()
    try:
        Data.peopledesc.AppendLine(line)
    except:
        Data.Lock.release()
        Utils.Error('Failed to register person:\n'+line)
        return Delegate('/errors/fatal.html',req,onlyhead)
    
    # Put new person into database in memory:
    p.lname = lname
    p.fname = fname
    p.sem = sem
    p.stud = stud
    p.passwd = passwd
    p.email = email
    p.wishes = wishes
    p.persondata1 = persondata1
    p.persondata2 = persondata2
    p.persondata3 = persondata3
    p.persondata4 = persondata4
    p.persondata5 = persondata5
    p.persondata6 = persondata6
    p.persondata7 = persondata7
    p.persondata8 = persondata8
    p.persondata9 = persondata9

    # The same person object stays in the "people" dictionary.
    Data.Lock.release()

    # At last write out a sensible response:
    Utils.Error('id '+id, prefix='SubmitRegChange: ')
    return Delegate('/messages/regchsuccess.html',req,onlyhead)

Site['/SubmitRegChange'] = FunWR(SubmitRegChange)

class EH_withPersSheet_class(EH_withPersData_class):
    '''This class exists to produce handlers that can fill in personal data
into an exercises sheet. It has some additional non-generic methods and holds
a Person object and a Sheet object as data.'''
    p = None    # here we store the concrete personal data
    s = None    # here we store the concrete sheet data
    r = 100     # resolution
    iamadmin = 0  # Flag, whether admin password was given
    def __init__(self,p,s,r):
        self.p = p
        self.s = s
        self.r = r
    def handle_SheetName(self,node,out):
        out.write(self.s.name)
    def handle_SheetNr(self,node,out):
        out.write(str(self.s.nr))
    def handle_IfOpen(self,node,out):
        if (not(self.s.IsClosed()) and (self.s.openfrom == None or 
            time.time() >= self.s.openfrom)) or self.iamadmin:  # Sheet is open
            # Write out tree recursively:
            if node[2] != None:
                for n in node[2]:
                    XMLRewrite.XMLTreeRecursion(n,self,out)
    def handle_IfClosed(self,node,out):
        if self.s.IsClosed() and not(self.iamadmin):    
            # Sheet already closed
            # Write out tree recursively:
            if node[2] != None:
                for n in node[2]:
                    XMLRewrite.XMLTreeRecursion(n,self,out)
    def handle_HiddenIdOfPerson(self,node,out):
        out.write('<input type="hidden" name="id" value="'+self.p.id+'" />\n')
    def handle_HiddenNameOfSheet(self,node,out):
        out.write('<input type="hidden" name="sheet" value="'+self.s.name+
                  '" />\n')
    def handle_WebSheetTable(self,node,out):
        if self.p.mcresults.has_key(self.s.name):
            self.s.WebSheetTable(self.r,SeedFromId(self.p.id),out,
                                 self.p.mcresults[self.s.name])
        else:
            self.s.WebSheetTable(self.r,SeedFromId(self.p.id),out,None)
    def handle_OpenTo(self,node,out):
        out.write(LocalTimeString(self.s.opento))
    def handle_OpenFrom(self,node,out):
        if self.s.openfrom:
            out.write(LocalTimeString(self.s.openfrom))
    def handle_StatisticsTable(self, node, out):
        numberOfPeople, numberOfSubmissions, statistics = self.s.Statistics()
        out.write('<table class="statistics">\n')
        out.write('<tr><th>Ex</th><th>Qu</th><th>Var</th>'
            + '<th colspan="2">Seen By</th><th colspan="2">Tried By</th>'
              '<th colspan="2">Solved By</th></tr>')
        if len(statistics) > 0:
            exnr_old, qnr_old, vnr, presented, tried, solved = statistics[0]
        for exnr, qnr, vnr, presented, tried, solved in statistics:
            out.write('<tr')
            if exnr > exnr_old:
                out.write(' class="extrenner"')
                exnr_old = exnr
                qnr_old = qnr
            elif qnr > qnr_old:
                out.write(' class="qutrenner"')
                qnr_old = qnr
            out.write('>')
            out.write('<td>%d</td><td>%d</td><td>%d</td>' % (exnr,qnr,vnr))
            if numberOfPeople > 0:
                out.write('<td>%d</td><td>%.2f%%</td>' % (presented, 
                              (float(100*presented)/float(numberOfPeople))))
            else:
                out.write('<td>%d</td><td></td>' % presented )
            if presented > 0:
                pc = float(tried)/float(presented)
                out.write('<td>%d</td><td %s>%.2f%%</td>' % 
                          (tried, ClassFromFraction(pc) ,100.0*pc))
            else:
                out.write('<td>%d</td><td>0 %%</td>' % tried)
            if tried > 0:
                pc = float(solved)/float(tried)
                out.write('<td>%d</td><td %s>%.2f%%</td>' % 
                               (solved, ClassFromFraction(pc), 100*pc ))
            else:
                out.write('<td>%d</td><td>0</td>' % solved)
            out.write('</tr>\n')
        out.write('</table>')
    def handle_ScoresTableByGroup(self, node, out):
        hwStr = '<h3>Homework</h3>'
        mcStr = '<h3>Multiple Choice</h3>'
        l = Utils.SortNumerAlpha(Data.groups.keys())
        for grp in l:
            numHw, avHw, medHw, highHw, listHw, \
            numMc, avMc, medMc, highMc, listMc = \
                 Data.GlobalStatistics(self.s.name, grp)
            hwStr += '<h4>Group: %s</h4>\n' % grp                
            hwStr += '<p>Median: %.2f, Average: %.2f </p>' % (medHw, avHw)
            hwStr += DistributionTable(numHw, listHw)
            mcStr += '<h4>Group: %s</h4>\n' % grp
            mcStr += '<p>Median: %.2f, Average: %.2f </p>' % (medMc, avMc)
            mcStr += DistributionTable(numMc, listMc)
        out.write(hwStr)
        out.write(mcStr)

def ClassFromFraction(pc):
    # pc should be a float. Meaningful results only with 0<=pc<=1
    # Returns string with CSS-"class"-statement, corresponding to pc
    # col0 - col100 with stepwidth 5
    try:
        pc = float(pc)
        if pc < 0: pc = 0
        if pc > 1: pc = 1
    except:
        return ''
    pc = int (pc * 100)
    col  = (pc / 5) * 5
    return ' class="col' + str(col) + '" '


def SeedFromId(id):
    return hash(id)   # is this guaranteed to return the same number for
                      # the same string?

def QuerySheet(req,onlyhead):
    # First check whether the id is valid:
    id = req.query.get('id',[''])[0].strip()   # our default id
    if not(Config.conf['IdCheckRegExp'].match(id)):
        return Delegate('/errors/invalidid.html',req,onlyhead)

    # Then check whether we already have someone with that id:
    if not(Data.people.has_key(id)):
        return Delegate('/errors/idunknown.html',req,onlyhead)
        
    p = Data.people[id]
    iamadmin = Authenticate(p,req,onlyhead)
    if iamadmin < 0:
        return Delegate('/errors/wrongpasswd.html',req,onlyhead)

    format = req.query.get('format',['HTML'])[0]  # Can be "HTML" or "PDF"
    pdftable = req.query.get('pdftable',['yes'])[0] # Can also be "no"
    sheetname = req.query.get('sheet',[''])[0].strip()  # the name of a sheet
    # Search for this name among sheet names:
    l = Exercises.SheetList()
    i = 0
    while i < len(l) and l[i][1] != sheetname: 
        i += 1
    if i >= len(l) or (not(iamadmin) and l[i][2].openfrom and 
                       time.time() < l[i][2].openfrom):
        return Delegate('/errors/unknownsheet.html',req,onlyhead)
    sheet = l[i]
    if format == 'HTML':
        resolution = req.query.get('resolution',['Standard'])[0]
        addheader = []   # If resolution chosen explicitly, store it in cookie
        if resolution == 'Standard':
            resolution = Config.conf['Resolutions'][0]   # the default
            try:
                # Check for cookie:
                cookie = Cookie.SimpleCookie()
                cookie.load('Cookie: '+req.headers.get('Cookie',''))
                cookieres = cookie['OKUSONResolution'].value
                resolution = int(cookieres)
                if not(resolution in Config.conf['Resolutions']):
                    resolution = Config.conf['Resolutions'][0]
            except:
                pass
        else:
            try: 
                resolution = int(resolution)
                if not(resolution in Config.conf['Resolutions']):
                    resolution = Config.conf['Resolutions'][0]
                else:
                    addheader = [('Set-Cookie',
                       'OKUSONResolution='+str(resolution)+
                       ';Path:/;Max-Age=7862400;Version=1')]
                    # Max-Age is 13 weeks, for one semester
            except: 
                resolution = Config.conf['Resolutions'][0]
               
        # Now we really deliver the sheet. We must create a handler object
        # for person p's sheet l[i]:
        handler = EH_withPersSheet_class(p,sheet[2],resolution)
        handler.iamadmin = iamadmin
        Utils.Error('id '+id+', sheet '+sheet[2].name+' as HTML', 
                    prefix='QuerySheet: ')
        return Delegate('/sheet.html',req,onlyhead,handler,addheader)
    elif format == 'PDF':
        # Collect placeholder values in dictionary
        values = {}
        values['SheetName'] = sheetname
        values['IdOfPerson'] = id
        for a in ['CourseName', 'Semester', 'Lecturer', 'ExtraLaTeXHeader']:
          values[a] = Config.conf[a]
        # find values of custom variables from config and for persons
        for i in range(9):
          ii = str(i+1)
          if Config.conf.has_key('User'+ii):
            values['User'+ii] = Config.conf['User'+ii]
          else:
            values['User'+ii] = ''
          try:
            values['PersonData'+ii] = getattr(Data[id], 'persondata'+ii)
          except:
            values['PersonData'+ii] = ''
        values['OpenTo'] = LocalTimeString(sheet[2].opento)
        if sheet[2].openfrom:
            values['OpenFrom'] = LocalTimeString(sheet[2].openfrom)
        else:
            values['OpenFrom'] = ''
        values['CurrentTime'] = LocalTimeString()

        # finally the actual exercises as longtable environment or text
        if pdftable == 'no':
            if hasattr(sheet[2], 'cachedPDF'):
                pdf = sheet[2].cachedPDF
            else:
                values['ExercisesNoTable'] = sheet[2].LatexSheetNoTable()
                latexinput = SimpleTemplate.FillTemplate(
                               Config.conf['PDFTemplateNoTable'], values)
                pdf = LatexImage.LatexToPDF(latexinput)
                sheet[2].cachedPDF = pdf
        else: 
            values['ExercisesTable'] = sheet[2].LatexSheetTable(SeedFromId(id))
            latexinput = SimpleTemplate.FillTemplate(
                               Config.conf['PDFTemplate'], values)
            pdf = LatexImage.LatexToPDF(latexinput)

        if not pdf:
            Utils.Error('Cannot pdflatex sheet input (id='+id+\
                        ', sheet='+sheetname+').')
            return Delegate('/errors/pdfproblem.html', req, onlyhead)
        Utils.Error('id '+id+', sheet '+sheet[2].name+' as PDF', 
                    prefix='QuerySheet: ')
        return ({'Content-type': 'application/pdf', 'Expires': 'now',
                 'Content-Disposition': 'attachment; filename="sheet_%s.pdf"' % sheet[2].name}, pdf)
    else:
        return Delegate('/errors/invalidformat.html', req, onlyhead)

Site['/QuerySheet'] = FunWR(QuerySheet)

def SubmitSheet(req,onlyhead):
    '''This function accepts a submission for a sheet. It checks the
input, gives appropriate warning and error messages and stores the
submission as well as the results.'''

    # First check whether the id is valid:
    id = req.query.get('id',[''])[0].strip()   # our default id
    if not(Config.conf['IdCheckRegExp'].match(id)):
        return Delegate('/errors/invalidid.html',req,onlyhead)

    # Then check whether we already have someone with that id:
    if not(Data.people.has_key(id)):
        return Delegate('/errors/idunknown.html',req,onlyhead)
        
    p = Data.people[id]
    iamadmin = Authenticate(p,req,onlyhead)
    if iamadmin < 0:
        return Delegate('/errors/wrongpasswd.html',req,onlyhead)

    sheetname = req.query.get('sheet',[''])[0]    # the name of a sheet
    # Search for this name among sheet names:
    l = Exercises.SheetList()
    i = 0
    while i < len(l) and l[i][1] != sheetname: 
        i += 1
    s = l[i][2]   # the sheet in question
    if i >= len(l) or (not(iamadmin) and s.openfrom and 
                       time.time() < s.openfrom):
        return Delegate('/errors/unknownsheet.html',req,onlyhead)

    # Now check, whether it is still possible to submit this sheet:
    if s.IsClosed() and not(iamadmin):
        return Delegate('/errors/sheetclosed.html',req,onlyhead)

    ok = s.AcceptSubmission(p,SeedFromId(p.id),req.query)
    if not(ok):
        Utils.Error('bad submission, id '+id+', sheet '+sheetname, 
                    prefix='SubmitSheet: ')
        return Delegate('/error/badsubmission.html',req,onlyhead)
    else:
        handler = EH_withPersSheet_class(p,s,Config.conf['Resolutions'][0])
        handler.iamadmin = iamadmin
        Utils.Error('successful submission, id '+id+', sheet '+sheetname, 
                    prefix='SubmitSheet: ')
        return Delegate('/messages/subsuccess.html',req,onlyhead,handler)

Site['/SubmitSheet'] = FunWR(SubmitSheet)

def QueryResults(req,onlyhead):
    '''This function is called when a user asks to see his results.
It will work on the submitted form data, check whether a registration is
there and send a form to display and change the saved data.'''
    # First check whether the id is valid:
    id = req.query.get('id',[''])[0].strip()   # our default id
    if not(Config.conf['IdCheckRegExp'].match(id)):
        return Delegate('/errors/invalidid.html',req,onlyhead)

    # Then check whether we already have someone with that id:
    if not(Data.people.has_key(id)):
        return Delegate('/errors/idunknown.html',req,onlyhead)
        
    p = Data.people[id]
    iamadmin = Authenticate(p,req,onlyhead)
    if iamadmin < 0:
        return Delegate('/errors/wrongpasswd.html',req,onlyhead)

    currentHandler = EH_withPersData_class(p)
    Utils.Error('id '+id, prefix='QueryResults: ')
    return Delegate('/results.html',req,onlyhead,currentHandler)

Site['/QueryResults'] = FunWR(QueryResults)

#######################################################################
# This is for tutoring group specific pages:

class EH_withGroupInfo_class(EH_Generic_class):
    grp = None
    def __init__(self,grp):
        self.grp = grp
    def handle_GroupNumber(self,node,out):
        out.write(str(self.grp.number))
    def handle_GroupTutor(self,node,out):
        out.write(str(self.grp.tutor))
    def handle_GroupPlace(self,node,out):
        out.write(str(self.grp.place))
    def handle_GroupTime(self,node,out):
        out.write(str(self.grp.time))
    def handle_GroupEmailTutor(self,node,out):
        out.write(str(self.grp.emailtutor))
    def handle_GroupInfo1(self,node,out):
        out.write(str(self.grp.groupinfo1))
    def handle_GroupInfo2(self,node,out):
        out.write(str(self.grp.groupinfo2))
    def handle_GroupInfo3(self,node,out):
        out.write(str(self.grp.groupinfo3))
    def handle_GroupInfo4(self,node,out):
        out.write(str(self.grp.groupinfo4))
    def handle_GroupInfo5(self,node,out):
        out.write(str(self.grp.groupinfo5))
    def handle_GroupInfo6(self,node,out):
        out.write(str(self.grp.groupinfo6))
    def handle_GroupInfo7(self,node,out):
        out.write(str(self.grp.groupinfo7))
    def handle_GroupInfo8(self,node,out):
        out.write(str(self.grp.groupinfo8))
    def handle_GroupInfo9(self,node,out):
        out.write(str(self.grp.groupinfo9))
    def handle_GroupIDs(self,node,out):
        l = Utils.SortNumerAlpha(self.grp.people)
        out.write(string.join(l, ', '))

    def handle_ScoresTable(self, node, out):
        out.write('<table class="scorestable">\n')
        out.write('<tr><th></th><th colspan="4">Homework Scores</th>'
                  '<th colspan="4">Multiple Choice Scores</th></tr>')
        out.write('<tr><th>Sheet</th><th>#Subm.</th><th>Avg.</th>' )
        out.write( '<th>Median</th><th>Highest</th>')
        out.write(' <th>#Subm.</th><th>Avg.</th>' )
        out.write( '<th>Median</th><th>Highest</th>  </tr>')
        listOfTables = []
        for sheetNumber, sheetName, sheet in Exercises.SheetList():
            if self.grp != None:
                group = str(self.grp.number)
            else:
                group = None
            numHw, avHw, medHw, highHw, listHw, \
            numMc, avMc, medMc, highMc, listMc = \
                   Data.GlobalStatistics(sheetName, group)
            out.write('<tr>')
            out.write('<td>%s</td>' % sheetName )
            out.write('<td>%d</td><td>%.2f</td><td>%.2f</td><td>%d</td>'
                      % (numHw, avHw, medHw, highHw) )
            out.write('<td>%d</td><td>%.2f</td><td>%.2f</td><td>%d</td>'
                      % (numMc, avMc, medMc, highMc) )
            out.write('</tr>\n')
            
            exStr = '<h2>Overview for sheet %s</h2>\n' % sheetName
            
            for num, av, med, list, heading in \
                [ (numHw, avHw, medHw, listHw, 'Homework'), \
                  (numMc, avMc, medMc, listMc, 'Multiple Choice')]:
                exStr +='<h3>' + heading + '</h3>'
                exStr +='<p>Median: %.2f, Average: %.2f</p>' % (med, av)
                exStr += DistributionTable(num, list)
            listOfTables.append(exStr)
        out.write('</table>\n')
        for s in listOfTables:
            out.write(s)

def DistributionTable(num, list):
    exStr = ''
    if num > 0:
        exStr +='<table class="pointdistribution">\n'
        row1 = '<tr class="pddata">'
        row2 = '<tr class="pdtext">'
        row3 = '<tr class="pdpercentage">'
        row4 = '<tr class="pdindex">'
        try: 
            scalefactor = 200 / max(list)
            if scalefactor < 1: 
                scalefactor = 1
        except:
            scalefactor = 1
        for i in range(len(list)):
            row1 += '<td><img src="/images/red.png" alt="" width="10px" '\
                    'height="' + str(list[i] * scalefactor) + 'px" /></td>'
            row2 += '<td>%d</td>' % list[i]
            try:
                row3 += '<td>%d</td>' % (100*float(list[i]) / float(num))
            except:
                row3 += '<td>0%</td>'
            row4 +=  '<td>%d</td>' % i 
        row1 += '<td class="summary"></td>'
        row2 += '<td class="summary">Sum: %d</td>' % num
        row3 += '<td class="summary">%</td>'
        row4 += '<td class="summary"></td>'
        exStr +=   row1 +'</tr>\n' + row2 + '</tr>\n' + row3 + '</tr>\n' + \
                   row4 +'</tr>\n' 
        exStr += '</table>\n\n' 
    return exStr
    
       
def GroupInfo(req, onlyhead):
    try:
        grp = Data.groups[req.query['number'][0]]
    except:
        grp = None
    if grp:
        handler = EH_withGroupInfo_class(grp)
        return Delegate('/groupinfo.html', req, onlyhead, handler)
    else:
        return Delegate('/errors/unknowngroup.html',req,onlyhead)
    
Site['/GroupInfo'] = FunWR(GroupInfo)

def ExamRegistration(req, onlyhead):
    # First check whether the id is valid:
    id = req.query.get('id',[''])[0].strip()   # our default id
    if not(Config.conf['IdCheckRegExp'].match(id)):
        return Delegate('/errors/invalidid.html',req,onlyhead)

    # Then check whether we already have someone with that id:
    if not(Data.people.has_key(id)):
        return Delegate('/errors/idunknown.html',req,onlyhead)
        
    p = Data.people[id]
    iamadmin = Authenticate(p,req,onlyhead)
    if iamadmin < 0:
        return Delegate('/errors/wrongpasswd.html',req,onlyhead)

    # Now check whether we have registration or un-registration:
    if req.query.get('anoderab',['an'])[0] == 'an':
        anmeld = 1
    else:
        anmeld = 0

    # Check number of exam:
    try:
        examnr = int(req.query.get('examnr',['0'])[0])
        if examnr < 0: examnr = 0
        elif examnr >= 24: examnr = 0
    except:
        examnr = 0

    # Now put information into database:
    timestamp = int(time.time())
    line = AsciiData.LineTuple( (id,str(examnr),str(anmeld),str(timestamp)) )
    Data.Lock.acquire()
    try:
        Data.examregdesc.AppendLine(line)
    except:
        Data.Lock.release()
        Utils.Error('Failed to register person for exam:\n'+line)
        return Delegate('/errors/fatal.html',req,onlyhead)
    while len(p.exams) < examnr+1: p.exams.append(None)
    if p.exams[examnr] == None:
        p.exams[examnr] = Data.Exam()
    p.exams[examnr].timestamp = timestamp
    p.exams[examnr].registration = anmeld
    Data.Lock.release()

    # At last write out a sensible response:
    Utils.Error('registered '+id+' for exam '+str(examnr),
                prefix='ExamRegistration: ' )
    return Delegate('/messages/examregsucc.html',req,onlyhead)

Site['/ExamRegistration'] = FunWR(ExamRegistration)

#######################################################################
# The following is for the tutor's pages:

class EH_withGroupAndSheet_class(EH_withGroupInfo_class):
    '''This class exists to produce handlers that can fill data from a
       group and a sheet. It holds a group object and a sheet object.'''
    s = None    # A sheet object
    def __init__(self,g,s):
        self.grp = g   # this we owe our base class
        self.s = s
    def handle_SheetName(self,node,out):
        out.write(self.s.name)
    def handle_SheetNumber(self,node,out):
        out.write(str(self.s.nr))
    def handle_HiddenNameOfSheet(self,node,out):
        out.write('<input type="hidden" name="sheet" value="'+self.s.name+
                  '" />\n')
    def handle_HiddenNumberOfGroup(self,node,out):
        out.write('<input type="hidden" name="group" value="'+
                  str(self.grp.number)+'" />\n')
    def handle_HomeworkSheetInput(self,node,out):
        l = Utils.SortNumerAlpha(self.grp.people)
        s = self.s
        counter = 0
        for k in l:
            if Data.people.has_key(k):
                counter += 1
                p = Data.people[k]
                if p.homework.has_key(s.name) and s.openfrom < time.time():
                    default = str(p.homework[s.name].totalscore)
                    default2 = p.homework[s.name].scores
                else:
                    default = ''
                    default2 = ''
                if counter % 5 == 0:
                  out.write('<tr><td class="trenner">'+k+'</td>'
                            '<td class="trenner">'+p.lname+', '+p.fname+'</td>'
                            '<td class="trenner">'
                            '<input size="6" maxlength="6"'
                            ' name="P'+k+'" value="'+default+'" /></td>\n'
                            '    <td class="trenner"><input size="30" '
                            'maxlength="60" name="S'+k+
                            '" value="'+default2+'" /></td></tr>\n')
                else:
                  out.write('<tr><td>'+k+'</td><td>'+p.lname+', '+p.fname+
                            '</td><td><input size="6" maxlength="6"'
                            ' name="P'+k+'" value="'+default+'" /></td>\n'
                            '   <td><input size="30" maxlength="60" name="S'+k+
                            '" value="'+default2+'" /></td></tr>\n')
    
class EH_withGroupAndPerson_class(EH_withGroupInfo_class,EH_withPersData_class):
    '''This class exists to produce handlers that can fill data from a
       group and personal data. It holds a group object and a Person object.'''
    def __init__(self,g,p):
        self.grp = g   # this we owe our base class
        self.p = p     # this also is used by base class methods
    def handle_HiddenIdOfPerson(self,node,out):
        out.write('<input type="hidden" name="id" value="'+self.p.id+'" />\n')
    def handle_HiddenNumberOfGroup(self,node,out):
        out.write('<input type="hidden" name="group" value="'+
                  str(self.grp.number)+'" />\n')
    def handle_HomeworkPersonInput(self,node,out):
        sl = Exercises.SheetList()
        counter = 0
        for nr,na,s in sl:
            counter += 1
            if self.p.homework.has_key(na):
                default = str(self.p.homework[na].totalscore)
                default2 = self.p.homework[na].scores
            else:
                default = ''
                default2 = ''
            if counter % 5 == 0:
                out.write('<tr><td class="trenner">'+na+'</td>'
                          '<td class="trenner"><input size="6" maxlength="6"'
                          ' name="S'+na+'" value="'+default+'" /></td>\n'
                          '    <td class="trenner"><input size="30" '
                          'maxlength="60" name="T'+na+
                          '" value="'+default2+'" /></td></tr>\n')
            else:
                out.write('<tr><td>'+na+'</td><td><input size="6" maxlength="6"'
                          ' name="S'+na+'" value="'+default+'" /></td>\n'
                          '    <td><input size="30" maxlength="60" name="T'+na+
                          '" value="'+default2+'" /></td></tr>\n')


def TutorRequest(req,onlyhead):
    '''This handles a request from a tutor via the tutor page. This means
       a possible password change and/or a request for an input page.'''
    # First verify validity of group number:
    groupnr = req.query.get('group',['0'])[0]
    try:
        groupnr = int(groupnr)
    except:
        groupnr = 0
    if groupnr < 0 or not(Data.groups.has_key(str(groupnr))):
        return Delegate('/errors/badgroupnr.html',req,onlyhead)

    g = Data.groups[str(groupnr)]
    # Now verify the password for this group:
    iamadmin = AuthenticateTutor(g,req,onlyhead)
    if iamadmin < 0:
        return Delegate('/errors/wrongpasswd.html',req,onlyhead)

    # Now check whether the two new passwords are identical:
    pw1 = req.query.get('pw1',[''])[0].strip()[:16]
    pw2 = req.query.get('pw2',[''])[0].strip()[:16]
    if pw1 != '' or pw2 != '':
        if pw1 != pw2:
            return Delegate('/errors/diffpasswd.html',req,onlyhead)
        salt = random.choice(string.letters) + random.choice(string.letters)
        passwd = crypt.crypt(pw1,salt)
        # Now change password for this group:
        line = AsciiData.LineTuple( (str(groupnr), passwd, g.tutor, g.place,
                                     g.time, g.emailtutor, g.groupinfo1,
                                     g.groupinfo2, g.groupinfo3, g.groupinfo4,
                                     g.groupinfo5, g.groupinfo6, g.groupinfo7,
                                     g.groupinfo8, g.groupinfo9) )
        Data.Lock.acquire()
        try:
            Data.groupinfodesc.AppendLine(line)
        except:
            Data.Lock.release()
            Utils.Error('Failed to change group password:\n'+line)
            return Delegate('/errors/fatal.html',req,onlyhead)
        g.passwd = passwd
        Data.Lock.release()
    
    # Now password is changed (or not), decide about input request:
    sheet = req.query.get('sheet',[''])[0].strip()
    if sheet != '':
        sl = Exercises.SheetList()
        i = 0
        while i < len(sl) and sl[i][1] != sheet: i += 1
        if i < len(sl) and (sl[i][2]==None or sl[i][2].openfrom < time.time()):
            # we know this sheet!
            handler = EH_withGroupAndSheet_class(g,sl[i][2])
            return Delegate('/edithomeworksheet.html',req,onlyhead,handler)
        else:
            return Delegate('/errors/tutunknownsheet.html',req,onlyhead)

    id = req.query.get('id',[''])[0]
    if id == '':   # we do nothing
        return Delegate('/tutors.html',req,onlyhead)

    if not(Config.conf['IdCheckRegExp'].match(id)):
        return Delegate('/errors/invalidid.html',req,onlyhead)

    # Then check whether we already have someone with that id:
    if not(Data.people.has_key(id)):
        return Delegate('/errors/idunknown.html',req,onlyhead)
        
    p = Data.people[id]
    if p.group != groupnr:
        return Delegate('/errors/idnotingroup.html',req,onlyhead)

    handler = EH_withGroupAndPerson_class(g,p)
    return Delegate('/edithomeworkperson.html',req,onlyhead,handler)

Site['/TutorRequest'] = FunWR(TutorRequest)


def SubmitHomeworkSheet(req,onlyhead):
    '''This accepts the input by a tutor for his group for one sheet.'''
    # First verify validity of group number:
    groupnr = req.query.get('group',['0'])[0]
    try:
        groupnr = int(groupnr)
    except:
        groupnr = 0
    if groupnr < 0 or not(Data.groups.has_key(str(groupnr))):
        return Delegate('/errors/badgroupnr.html',req,onlyhead)

    g = Data.groups[str(groupnr)]
    # Now verify the password for this group:
    iamadmin = AuthenticateTutor(g,req,onlyhead)
    if iamadmin < 0:
        return Delegate('/errors/wrongpasswd.html',req,onlyhead)

    # Now look for the sheet:
    sheet = req.query.get('sheet',[''])[0]
    sl = Exercises.SheetList()
    i = 0
    while i < len(sl) and sl[i][1] != sheet: i += 1
    if i < len(sl):   # we know this sheet!
        # Now we have sheet and group and authentication, read off results:
        s = sl[i][2]
        Data.Lock.acquire()
        for k in g.people:
            if Data.people.has_key(k):
                p = Data.people[k]
                score = req.query.get('P'+k,[''])[0]
                scores = req.query.get('S'+k,[''])[0]
                try:
                    if '.' in score:
                        totalscore = float(score)
                    else:
                        totalscore = int(score)
                except:
                    totalscore = 0
                if p.homework.has_key(s.name) or score != '':
                    # We only work, if either the input is non-empty or
                    # if there was already a result. This allows for
                    # deletion of results.
                    line = AsciiData.LineTuple( 
                                 (p.id, s.name, str(totalscore),scores) )
                    try:
                        Data.homeworkdesc.AppendLine(line)
                    except:
                        Data.Lock.release()
                        Utils.Error('Failed store homework result:\n'+line)
                        return Delegate('/errors/fatal.html',req,onlyhead)
                    if not(p.homework.has_key(s.name)):
                        p.homework[s.name] = Data.Homework()
                    p.homework[s.name].totalscore = totalscore
                    p.homework[s.name].scores = scores
        Data.Lock.release()
        return Delegate('/tutors.html',req,onlyhead)
    else:
        return Delegate('/errors/tutunknownsheet.html',req,onlyhead)

Site['/SubmitHomeworkSheet'] = FunWR(SubmitHomeworkSheet)

def SubmitHomeworkPerson(req,onlyhead):
    '''This accepts the input by a tutor for his group for one person.'''
    # First verify validity of group number:
    groupnr = req.query.get('group',['0'])[0]
    try:
        groupnr = int(groupnr)
    except:
        groupnr = 0
    if groupnr < 0 or not(Data.groups.has_key(str(groupnr))):
        return Delegate('/errors/badgroupnr.html',req,onlyhead)

    g = Data.groups[str(groupnr)]
    # Now verify the password for this group:
    # We use the function for people, this is possible because g as a
    # data field "passwd".
    iamadmin = AuthenticateTutor(g,req,onlyhead)
    if iamadmin < 0:
        return Delegate('/errors/wrongpasswd.html',req,onlyhead)

    # Now look for the person:
    id = req.query.get('id',[''])[0]
    if not(Config.conf['IdCheckRegExp'].match(id)):
        return Delegate('/errors/invalidid.html',req,onlyhead)

    # Then check whether we already have someone with that id:
    if not(Data.people.has_key(id)):
        return Delegate('/errors/idunknown.html',req,onlyhead)
        
    p = Data.people[id]
    sl = Exercises.SheetList()
    # Now we have person and group and authentication, read off results:
    Data.Lock.acquire()
    for nr,na,s in sl:
        if s.counts and s.openfrom < time.time():
            score = req.query.get('S'+na,[''])[0]
            scores = req.query.get('T'+na,[''])[0]
            try:
                if '.' in score:
                    totalscore = float(score)
                else:
                    totalscore = int(score)
            except:
                totalscore = 0
            if p.homework.has_key(na) or score != '':
                # We only work, if either the input is non-empty or
                # if there was already a result. This allows for
                # deletion of results.
                line = AsciiData.LineTuple( 
                             (p.id, s.name, str(totalscore),scores) )
                try:
                    Data.homeworkdesc.AppendLine(line)
                except:
                    Data.Lock.release()
                    Utils.Error('Failed store homework result:\n'+line)
                    return Delegate('/errors/fatal.html',req,onlyhead)
                if not(p.homework.has_key(s.name)):
                    p.homework[s.name] = Data.Homework()
                p.homework[s.name].totalscore = totalscore
                p.homework[s.name].scores = scores
    Data.Lock.release()
    return Delegate('/tutors.html',req,onlyhead)

Site['/SubmitHomeworkPerson'] = FunWR(SubmitHomeworkPerson)


#######################################################################
# The following is for the administrator's pages:

def AdminLogin(req,onlyhead):
    global currentcookie
    passwd = req.query.get('passwd',[''])[0]
    salt = Config.conf['AdministratorPassword'][:2]
    passwd = crypt.crypt(passwd,salt)
    if passwd != Config.conf['AdministratorPassword']:
        return Delegate('/errors/wrongpasswd.html',req,onlyhead)

    random.seed(time.time())
    currentcookie = str(random.randrange(10000000))
    (header,content) = Site['/adminmenu.html'].getresult(req,onlyhead)
    header['Set-Cookie'] = 'OKUSON='+currentcookie+ \
         ';Path=/;Max-Age=3600;Version=1'
         # Max-Age is one hour
    #header['Location'] = '/adminmenu.html'
    # Taken out to please opera, which does not get the cookie for the
    # login with this header. Max.
    return (header,content)

Site['/AdminLogin'] = FunWR(AdminLogin)
Site['/AdminLogin'].access_list = Config.conf['AdministrationAccessList']

def AdminLogout(req,onlyhead):
    global currentcookie
    currentcookie = None
    return Delegate('/adminlogin.html',req,onlyhead)

Site['/AdminLogout'] = FunWR(AdminLogout)
Site['/AdminLogout'].access_list = Config.conf['AdministrationAccessList']

def Restart(req,onlyhead):
    '''If administrator can authorize, the server is restarted.'''
    if Authenticate(None,req,onlyhead) < 0:
        return Delegate('/errors/notloggedin.html',req,onlyhead)
    BuiltinWebServer.SERVER.raus = 1
    BuiltinWebServer.SERVER.restartcommand = \
          os.path.join(Config.home,'server/Server.py')
    os.kill(BuiltinWebServer.SERVER.ourpid,signal.SIGUSR1)
    return Delegate('/adminrestarted.html',req,onlyhead)
    
Site['/Restart'] = FunWR(Restart)
Site['/Restart'].access_list = Config.conf['AdministrationAccessList']

def Shutdown(req,onlyhead):
    '''If administrator can authorize, the server is shut down.'''
    if Authenticate(None,req,onlyhead) < 0:
        return Delegate('/errors/notloggedin.html',req,onlyhead)
    BuiltinWebServer.SERVER.raus = 1
    os.kill(BuiltinWebServer.SERVER.ourpid,signal.SIGUSR1)
    return Delegate('/admindown.html',req,onlyhead)
    
Site['/Shutdown'] = FunWR(Shutdown)
Site['/Shutdown'].access_list = Config.conf['AdministrationAccessList']

def NormalizeWishes(w):
    '''Normalizes a wishlist. First the string is split at space and commas,
       then only those chunks are taken, that are a valid ID of some
       participant.'''
    w = w.split()
    wishlist = []
    for ww in w:
      for www in ww.split(','):
        if Data.people.has_key(www): wishlist.append(www)
    return string.join(wishlist,',')

def Protect(st):
    '''Protects a string by deleting all colons and substituting spaces
       for newlines. Necessary for export purposes to avoid malformed
       export files.'''
    return st.replace(':','').replace('\n',' ')

# Some sort functions:

def CmpByID(a,b):
    try:
        an = int(a)
        bn = int(b)
        return cmp(an,bn)
    except:
        return cmp(a,b)

def CmpByName(a,b):
    v = cmp(Data.people[a].lname,Data.people[b].lname)
    if v: return v
    return cmp(Data.people[a].fname,Data.people[b].fname)

def CmpByStudiengang(a,b):
    v = cmp(Data.people[a].stud,Data.people[b].stud)
    if v: return v
    return cmp(a,b)

def CmpBySemester(a,b):
    v = cmp(Data.people[a].sem,Data.people[b].sem)
    if v: return v
    return cmp(a,b)

def CmpByLengthOfWishlist(a,b):
    v = cmp(len(Data.people[a].wishes),len(Data.people[b].wishes))
    if v: return v
    return cmp(a,b)

def CmpByGroupAndName(a,b):
    v = cmp(Data.people[a].group,Data.people[b].group)
    if v: return v
    return CmpByName(a,b)

def CmpByGroupAndID(a,b):
    v = cmp(Data.people[a].group,Data.people[b].group)
    if v: return v
    return CmpByID(a,b)

sorttable = {'ID': CmpByID, 'name': CmpByName, 'Studiengang': CmpByStudiengang,
             'semester': CmpBySemester, 
             'length of wishlist': CmpByLengthOfWishlist,
             'group and ID': CmpByGroupAndID, 
             'group and name': CmpByGroupAndName}

def ExportPeopleForGroups(req,onlyhead):
    '''Export the list of all participants, sorted by ID, giving the
       following fields: 
         id:lname:fname:sem:stud:wishes:persondata1-9
       where wishes has been normalized into a comma separated list
       of existing id's. Colons have been deleted.'''
    global sorttable
    if Authenticate(None,req,onlyhead) < 0:
        return Delegate('/errors/notloggedin.html',req,onlyhead)
    meth = req.query.get('together',['all together'])[0]
    l = Data.people.keys()
    sortedby = req.query.get('sortedby',[''])[0]
    out = cStringIO.StringIO()
    out.write('# ID:last name:first name:semester:studies:wishes:pdata1-9\n')
    def writegroup(l,out):
        global sorttable
        if sorttable.has_key(sortedby):
            l.sort(sorttable[sortedby])
        else:
            l.sort(CmpByID)
        for k in l:
            # Exclude guest IDs:
            if not(Config.conf['GuestIdRegExp'].match(k)):
                p = Data.people[k]
                w = NormalizeWishes(p.wishes)
                out.write(k+':'+Protect(p.lname)+':'+Protect(p.fname)+':'+
                          str(p.sem)+':'+Protect(p.stud)+':'+w+':'+
                          Protect(p.persondata1)+':'+Protect(p.persondata2)+
                          ':'+Protect(p.persondata3)+':'+Protect(p.persondata4)+
                          ':'+Protect(p.persondata5)+':'+Protect(p.persondata6)+
                          ':'+Protect(p.persondata7)+':'+Protect(p.persondata8)+
                          ':'+Protect(p.persondata9)+'\n')
    if meth == 'all together':
        writegroup(l,out)
    else:
        # Go through all Studiengangs:
        done = {}
        for i in range(len(l)):
            p = Data.people[l[i]]
            if not(done.has_key(p.stud)):
                # we have not done this Studiengang, so do it:
                ll = [l[i]]
                for j in range(i+1,len(l)):
                    pp = Data.people[l[j]]
                    if pp.stud == p.stud:
                        ll.append(l[j])
                out.write('# New Studiengang: '+p.stud+'\n')
                writegroup(ll,out)
                out.write('\n')
                done[p.stud] = 1

    st = out.getvalue()
    out.close()
    head = {'Content-type':'text/okuson',
        'Content-Disposition':'attachment; filename="peoplelistforgroups.txt"',
        'Last-modified':req.date_time_string(time.time())}
    return (head,st)

Site['/ExportPeopleForGroups'] = FunWR(ExportPeopleForGroups)
Site['/ExportPeopleForGroups'].access_list = \
        Config.conf['AdministrationAccessList']

def ExportPeople(req,onlyhead):
    '''Export the list of all participants, sorted by ID with all their
       personal data plus their group number (may be 0). 
       Colons have been deleted and newlines replaced by spaces.'''
    global sorttable
    if Authenticate(None,req,onlyhead) < 0:
        return Delegate('/errors/notloggedin.html',req,onlyhead)
    l = Data.people.keys()
    sortedby = req.query.get('sortedby',[''])[0]
    if sorttable.has_key(sortedby):
        l.sort(sorttable[sortedby])
    else:
        l.sort(CmpByID)
    out = cStringIO.StringIO()
    out.write('# All participants:\n')
    out.write('# ID:name:fname:semester:stud:passwd:email:wishes:' 
              'pdata1:...:pdata9:group\n')
    out.write('# Time and date of export: '+LocalTimeString()+'\n')
    for k in l:
        # Exclude guest IDs:
        if not(Config.conf['GuestIdRegExp'].match(k)):
            p = Data.people[k]
            out.write(k+':'+Protect(p.lname)+':'+Protect(p.fname)+':'+
                      str(p.sem)+':'+Protect(p.stud)+':'+p.passwd+':'+
                      Protect(p.email)+':'+
                      Protect(p.wishes)+':'+Protect(p.persondata1)+':'+
                      Protect(p.persondata2)+':'+Protect(p.persondata3)+':'+
                      Protect(p.persondata4)+':'+Protect(p.persondata5)+':'+
                      Protect(p.persondata6)+':'+Protect(p.persondata7)+':'+
                      Protect(p.persondata8)+':'+Protect(p.persondata9)+':'+
                      str(p.group)+'\n')
    st = out.getvalue()
    out.close()
    head = {'Content-type':'text/okuson',
            'Content-Disposition':'attachment; filename="peoplelist.txt"',
            'Last-modified':req.date_time_string(time.time())}
    return (head,st)

Site['/ExportPeople'] = FunWR(ExportPeople)
Site['/ExportPeople'].access_list = Config.conf['AdministrationAccessList']

def ExportExamParticipants(req,onlyhead):
    '''Export list of participants for exam.'''
    global sorttable
    if Authenticate(None,req,onlyhead) < 0:
        return Delegate('/errors/notloggedin.html',req,onlyhead)

    examnr = req.query.get('examnr',['0'])[0]
    try:
        examnr = int(examnr)
        if examnr < 0: examnr = 0
        elif examnr >= 24: examnr = 0
    except:
        examnr = 0
        
    l = Data.people.keys()
    sortedby = req.query.get('sortedby',[''])[0]
    if sorttable.has_key(sortedby):
        l.sort(sorttable[sortedby])
    else:
        l.sort(CmpByID)

    out = cStringIO.StringIO()
    out.write('# All participants of exam number '+str(examnr)+':\n')
    out.write('# ID:name:fname:timestamp\n')
    out.write('# Time and date of export: '+LocalTimeString()+'\n')
    for k in l:
        # Exclude guest IDs:
        if not(Config.conf['GuestIdRegExp'].match(k)):
            p = Data.people[k]
            if len(p.exams) > examnr and p.exams[examnr] != None and \
               p.exams[examnr].registration == 1:
                ts = LocalTimeString(p.exams[examnr].timestamp)
                ts.replace(':','.')
                out.write(k+':'+Protect(p.lname)+':'+Protect(p.fname)+':'+
                          ts+'\n')
    st = out.getvalue()
    out.close()
    head = {'Content-type':'text/okuson',
            'Content-Disposition':'attachment; filename="examlist.txt"',
            'Last-modified':req.date_time_string(time.time())}
    return (head,st)

Site['/ExportExamParticipants'] = FunWR(ExportExamParticipants)
Site['/ExportExamParticipants'].access_list = \
      Config.conf['AdministrationAccessList']

def ShowExerciseStatistics(req,onlyhead):
    if Authenticate(None,req,onlyhead) < 0:
        return Delegate('/errors/notloggedin.html', req, onlyhead)

    sheet = req.query.get('sheet',[''])[0].strip()
    sl = Exercises.SheetList()
    i = 0
    while i < len(sl) and sl[i][1] != sheet: i+=1
    if i < len(sl):
        s = sl[i][2]
        handler = EH_withPersSheet_class(None,s,Config.conf['Resolutions'][0])
        return Delegate('/exercisestatistics.html', req, onlyhead, handler)
    else:
        return Delegate('/errors/unknownsheet.html', req, onlyhead)


Site['/ShowExerciseStatistics'] = FunWR(ShowExerciseStatistics)
Site['/ShowExerciseStatistics'].access_list = \
     Config.conf['AdministrationAccessList']

def ShowGlobalStatisticsPerGroup(req,onlyhead):
    if Authenticate(None,req,onlyhead) < 0:
        return Delegate('/errors/notloggedin.html', req, onlyhead)

    sheet = req.query.get('sheet',[''])[0].strip()
    sl = Exercises.SheetList()
    i = 0
    while i < len(sl) and sl[i][1] != sheet: i+=1
    if i < len(sl):
        s = sl[i][2]
        handler = EH_withPersSheet_class(None,s,Config.conf['Resolutions'][0])
        return Delegate('/globalstatisticspergroup.html',req,onlyhead,handler)
    else:
        return Delegate('/errors/unknownsheet.html', req, onlyhead)


Site['/ShowGlobalStatisticsPerGroup'] = FunWR(ShowGlobalStatisticsPerGroup)
Site['/ShowGlobalStatisticsPerGroup'].access_list = \
     Config.conf['AdministrationAccessList']


def ShowGlobalStatistics(req,onlyhead):
    '''This function handles the request for the global statistics '''
    if Authenticate(None,req,onlyhead) < 0:
        return Delegate('/errors/notloggedin.html',req,onlyhead)
    try:
        grp = Data.groups[req.query['group'][0]]
    except:
        grp = None
    handler = EH_withGroupInfo_class(grp)
    return Delegate('/globalstatistics.html',req,onlyhead, handler)
        
        
Site['/ShowGlobalStatistics'] = FunWR(ShowGlobalStatistics)
Site['/ShowGlobalStatistics'].access_list = Config.conf['AdministrationAccessList']

def ExportResults(req,onlyhead):
    '''Exports all results of all participants, including MC, homework and
       exams.'''
    global sorttable
    if Authenticate(None,req,onlyhead) < 0:
        return Delegate('/errors/notloggedin.html',req,onlyhead)
    l = Data.people.keys()
    sortedby = req.query.get('sortedby',[''])[0]
    if sorttable.has_key(sortedby):
        l.sort(sorttable[sortedby])
    else:
        l.sort(CmpByID)
    out = cStringIO.StringIO()
    out.write('# All results of all participants:\n')
    out.write('# ID:name:fname:group:totalmc:totalhome:total:gradetext:grade:'
              'examscores{:sheetname;mcscore;homescore}\n')
    out.write('# Time and date of export: '+LocalTimeString()+'\n')
    sl = Exercises.SheetList()
    for k in l:
        # Exclude guest IDs:
        if not(Config.conf['GuestIdRegExp'].match(k)):
            p = Data.people[k]
            # Calculate total points:
            mcscore = homescore = 0
            for nr,na,s in sl:
                if s.counts and s.IsClosed():   # sheet already closed
                    if p.mcresults.has_key(na):
                        mcscore += p.mcresults[na].score
                    if p.homework.has_key(na):
                        homescore += p.homework[na].totalscore
            exams = []
            exams1 = []
            for i in range(len(p.exams)):
                if p.exams[i] == None or p.exams[i].totalscore < 0:
                    exams.append('-;0')
                    exams1.append(0)
                else:
                    if Config.conf['ExamGradingActive'] == 0 or \
                       Config.conf['ExamGradingFunction'] == None:
                        (msg,grade) = ('',0)
                    else:
                        try:
                            (msg,grade) = Config.conf['ExamGradingFunction'] \
                                       (p,i)
                        except:
                            etype, value, tb = sys.exc_info()
                            lines = traceback.format_exception(etype,value,tb)
                            Utils.Error('Call of ExamGradingFunction raised '
                               'an exception, ID: '+p.id+', message:\n'+
                               string.join(lines))
                            (msg,grade) = ('',0)
                    exams.append(str(p.exams[i].totalscore)+';'+str(grade))
                    exams1.append(p.exams[i].totalscore)
            if Config.conf['GradingActive'] and \
               Config.conf['GradingFunction'] != None:
                try:
                    (msg,grade) = Config.conf['GradingFunction']  \
                                   (p,sl,mcscore,homescore,exams1)
                except:
                    etype, value, tb = sys.exc_info()
                    lines = traceback.format_exception(etype,value,tb)
                    Utils.Error('Call of GradingFunction raised an exception, '
                                'ID: '+p.id+', message:\n'+string.join(lines))
                    msg = ''
                    grade = 0
            else:
                msg = ''
                grade = 0
            exams = string.join(map(str,exams),';')
            out.write( p.id+':'+Protect(p.lname)+':'+Protect(p.fname)+':'+
                       str(p.group)+':'+str(mcscore)+':'+str(homescore)+':'+
                       str(mcscore+homescore)+':'+Protect(msg)+':'+
                       str(grade)+':'+exams )
            for nr,na,s in sl:
                if s.IsClosed():   # sheet already closed
                    out.write(':'+s.name+';')
                    if p.mcresults.has_key(na):
                        out.write(str(p.mcresults[na].score))
                    out.write(';')
                    if p.homework.has_key(na):
                        out.write(str(p.homework[na].totalscore))
            out.write('\n')
    st = out.getvalue()
    out.close()
    head = {'Content-type':'text/okuson',
            'Content-Disposition':'attachment; filename="results.txt"',
            'Last-modified':req.date_time_string(time.time())}
    return (head,st)

Site['/ExportResults'] = FunWR(ExportResults)
Site['/ExportResults'].access_list = Config.conf['AdministrationAccessList']


def DisplaySheets(req,onlyhead):
    '''Allow the administrator after authentication to see future sheets.'''
    if Authenticate(None,req,onlyhead) < 0:
        return Delegate('/errors/notloggedin.html',req,onlyhead)
    return Adminexquery.getresult(req, onlyhead)
    
Site['/DisplaySheets'] = FunWR(DisplaySheets)
Site['/DisplaySheets'].access_list = Config.conf['AdministrationAccessList']

def SendMessage(req,onlyhead):
    '''Take the message from the entry field and send it to participant with
       the given id. This means that this message will appear on the result
       page of the participant.'''
    if Authenticate(None,req,onlyhead) < 0:
        return Delegate('/errors/notloggedin.html',req,onlyhead)
    msgid = req.query.get('msgid',[''])[0]
    if not(Config.conf['IdCheckRegExp'].match(msgid)):
        return Delegate('/errors/invalidid.html',req,onlyhead)

    # Then check whether we already have someone with that id:
    if not(Data.people.has_key(msgid)):
        return Delegate('/errors/idunknown.html',req,onlyhead)
        
    # Now get the text:
    msgtext = req.query.get('msgtext',[''])[0]

    line = AsciiData.LineTuple( (msgid,msgtext) )
    Data.Lock.acquire()

    # Put new message into file on disk:
    try:
        Data.messagedesc.AppendLine(line)
    except:
        Data.Lock.release()
        Utils.Error('Failed to append message:\n'+line)
        return Delegate('/errors/fatal.html',req,onlyhead)

    # Put new message into database in memory:
    Data.people[msgid].messages.append(msgtext)
    Data.Lock.release()
    return Delegate('/adminmenu.html',req,onlyhead)

Site['/SendMessage'] = FunWR(SendMessage)
Site['/SendMessage'].access_list = Config.conf['AdministrationAccessList']

def DeleteMessages(req,onlyhead):
    '''Show all private messages of a given participant and allow to delete
       some of them.'''
    if Authenticate(None,req,onlyhead) < 0:
        return Delegate('/errors/notloggedin.html',req,onlyhead)
    msgid = req.query.get('msgid',[''])[0]
    if not(Config.conf['IdCheckRegExp'].match(msgid)):
        return Delegate('/errors/invalidid.html',req,onlyhead)

    # Then check whether we already have someone with that id:
    if not(Data.people.has_key(msgid)):
        return Delegate('/errors/idunknown.html',req,onlyhead)
        
    p = Data.people[msgid]
    currentHandler = EH_withPersData_class(p)
    return Delegate('/showmessages.html',req,onlyhead,currentHandler)

Site['/DeleteMessages'] = FunWR(DeleteMessages)
Site['/DeleteMessages'].access_list = Config.conf['AdministrationAccessList']

def DeleteMessagesDowork(req,onlyhead):
    '''Called from the display of messages of one person.'''
    if Authenticate(None,req,onlyhead) < 0:
        return Delegate('/errors/notloggedin.html',req,onlyhead)
    persid = req.query.get('id',[''])[0]
    if not(Config.conf['IdCheckRegExp'].match(persid)):
        return Delegate('/errors/invalidid.html',req,onlyhead)

    # Then check whether we already have someone with that id:
    if not(Data.people.has_key(persid)):
        return Delegate('/errors/idunknown.html',req,onlyhead)
        
    p = Data.people[persid]
    i = len(p.messages)-1
    while i >= 0:
        flag = req.query.get('msg'+str(i),['-'])[0]
        if flag == '+':   # should be deleted
            line = AsciiData.LineTuple( (p.id,'$'+p.messages[i]) )
            Data.Lock.acquire()
            try:
                Data.messagedesc.AppendLine(line)
            except:
                Data.Lock.release()
                Utils.Error('Failed to append deletion of message:\n'+line)
                return Delegate('/error/fatal.html',req,onlyhead)
            del p.messages[i]
            Data.Lock.release()
        i -= 1
    
    return Delegate('/adminmenu.html',req,onlyhead)


Site['/DeleteMessagesDowork'] = FunWR(DeleteMessagesDowork)
Site['/DeleteMessagesDowork'].access_list = \
        Config.conf['AdministrationAccessList']

def Resubmit(req,onlyhead):
    '''This function handles resubmission of all submissions for one sheet.
This is for the case that the "correct answers" were not entered correctly
in the first place.'''
    if Authenticate(None,req,onlyhead) < 0:
        return Delegate('/errors/notloggedin.html',req,onlyhead)
    # Now check the sheet number:
    sheet = req.query.get('sheet',[''])[0]
    sl = Exercises.SheetList()
    i = 0
    while i < len(sl) and sl[i][1] != sheet:
        i += 1
    if sheet == '' or i >= len(sl):
        return Delegate('/errors/admunknownsheet.html',req,onlyhead)
        
    s = sl[i][2]

    # Now run through all participants:
    for k in Data.people:
        p = Data.people[k]
        ok = s.Resubmit(p,SeedFromId(p.id))
        if not(ok):
            return Delegate('/error/badsubmission.html',req,onlyhead)
    
    return Delegate('/messages/resubsuccess.html',req,onlyhead)

Site['/Resubmit'] = FunWR(Resubmit)
Site['/Resubmit'].access_list = Config.conf['AdministrationAccessList']


def AdminWork(req,onlyhead):
    '''This function does the dispatcher work for the administrator
       actions.'''
    action = req.query.get('Action',[''])[0].strip()
    if action == 'PID':
        return ({'Content-type': 'text/plain'}, str(BuiltinWebServer.PID))
    return Delegate('/errors/nothingtosee.html',req,onlyhead)

Site['/AdminWork'] = FunWR(AdminWork)
Site['/AdminWork'].access_list = Config.conf['AdministrationAccessList']


# We register all the other .tpl files in our tree with EH_Generic handlers:

def visitor(arg,dirname,names):
    if dirname == os.path.join(DocRoot,"images"):
        names[:] = []
    for n in names:
        if n[-4:] == '.tpl':
            if dirname == DocRoot:
                ourpath = '/'+n[:-4]
            else:
                ourpath = os.path.join(dirname[len(DocRoot):]+'/',n[:-4])
            if not(Site.has_key(ourpath+'.html')):
                try:
                    Site[ourpath+'.html'] = PPXML(dirname,n,EH_Generic)
                except:
                    Utils.Error('Loading of '+ourpath+'.tpl was not '
                                'successful!')

# Release the lock:
BuiltinWebServer.SiteLock.release()


Adminexquery = None
def RegisterAllTpl():
    global Adminexquery
    BuiltinWebServer.SiteLock.acquire()
    os.path.walk(DocRoot,visitor,None)
    # Mark the administrator's pages:
    Site['/adminlogin.html'].access_list=Config.conf['AdministrationAccessList']
    Site['/adminmenu.html'].access_list=Config.conf['AdministrationAccessList']
    # Reinstall exquery.html for admin - includes not yet open sheets
    eh = EH_Generic_class()
    eh.iamadmin = 1
    Adminexquery = PPXML(DocRoot,'exquery.tpl',eh)
    # Copy the index file to hide things:
    Site['/messages'] = Site['/errors'] = Site['/'] = Site['/index.html']
    Site['/messages/'] = Site['/errors/'] = Site['/index.html']
    Site['/images'] = Site['/images/'] = Site['/index.html']
    for r in Config.conf['Resolutions']:
        Site['/images/dpi'+str(r)] = Site['/index.html']
        Site['/images/dpi'+str(r)+'/'] = Site['/index.html']
    BuiltinWebServer.SiteLock.release()


BuiltinWebServer.WebResponse.access_list = Config.conf['AccessList']
BuiltinWebServer.access_list = Config.conf['AccessList']

