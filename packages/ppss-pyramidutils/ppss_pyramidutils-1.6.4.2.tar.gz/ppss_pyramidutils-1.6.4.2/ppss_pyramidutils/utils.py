import logging
import types
#from six import PY2

l = logging.getLogger("ppss.pyramidutils")

import sys
#import types
PY2 = sys.version_info[0] == 2

if PY2:
    def is_nonstr_iter(v):
        return hasattr(v, '__iter__')
else:
    def is_nonstr_iter(v):
        if isinstance(v, str):
            return False
        return hasattr(v, '__iter__')
string = types.StringTypes if PY2 else str


class SettingsReader():
    myconf = []

    @classmethod
    def confended(cls, **kwargs):
        pass

    @classmethod
    def valueread(cls,prop,value):
        return value

    @classmethod
    def __getMyConf(cls,settings, prefix,defaultval=None,verbose=False,**kwargs):
        resvals = {}
        resdicts = {}
        #string = types.StringTypes if PY2 else str
        l.debug("reading conf for {}".format(prefix))
        if prefix:
            prefix = prefix+"."
        for k in cls.myconf:
            if isinstance(k, string):
                prop = k
                key = prefix+k
                default = getattr(cls, k, defaultval)
            else:
                try:
                    prop = k[0]
                    key = prefix+k[0]
                    default = k[1]
                except Exception:
                    l.warn("exception reading {}".format(k))
                    continue

            value = settings.get(key, default)
            value = cls.valueread(prop,value)
            if "." in prop:
                propparts = prop.split(".")

                dictname = propparts[0]
                dictkey = propparts[1]
                if dictname not in resdicts:
                    resdicts[dictname] = {}
                resdicts[dictname][dictkey] = value
            else:
                setattr(cls, prop, value)
                #if key in settings:
                if verbose:
                    l.debug("value of {key} set to: {val}".format(
                        key=prop, val=value))

        for key, value in resdicts.items():
            resvals[key]=value
            setattr(cls, key, value)
            if verbose:
                l.debug("value of {key} set to: {val}".format(key=key, val=value))
            #setattr(cls,k,unicode(settings[key]) )
        #for k in cls.myconf:
        #    if isinstance(k, string):
        #        key = k
        #    else:
        #        key = k[0]
        #    l.debug("val for {key} = {val}".format(
        #        key=key, val=getattr(cls, key)))
        return resvals

    def __getAllConf(cls,settings ,prefix,defaultval,verbose=False,**kwargs):
        prefixdotted = prefix + "." if prefix else ""
        prefixlen = len(prefixdotted)
        parse = kwargs.get('parse',{})
        resdicts = {}
        for k in settings.keys():
            if not k.startswith(prefixdotted):
                continue
            key = k[prefixlen:]
            value = settings.get(k)
            if key in parse:
                value = parse[key](value)
            resdicts[key]=value
            cls.myconf.append(key)
        for key, value in resdicts.items():
            setattr(cls, key, value)
            resvals[key]=value
            if verbose:
                l.debug("value of {key} set to: {val}".format(key=key, val=value))
        return resvals

    @staticmethod
    def valueAsList(value,resaslist = False,stripit = True,mapfunc=None):
        if not is_nonstr_iter(value):
            #print(repr(confval))
            value = aslist(value,flatten=False)
        if resaslist != False and isinstance(resaslist, string):
            value = value.split(resaslist)
            if stripit:
                value = map(str.strip,value)
            if mapfunc:
                value = map(mapfunc,value)
        return value


    @classmethod
    def config(cls, settings, prefix=None, defaultval=None,**kwargs):
        
        if not prefix:
            prefix = cls.__name__.lower()

        if cls.myconf:
            cls.__getMyConf(settings ,prefix,defaultval  )
        else:
            cls.__getAllConf(settings ,prefix,defaultval  )

        cls.confended()


    @classmethod
    def conf2dict(cls):
        valdict = {}
        for k in cls.myconf:
            if isinstance(k, string):
                prop = k
            else:
                prop = k[0]
            try:
                valdict[prop] = getattr(cls,prop)
            except Exception as e:
                l.exception(f"{prop} configured as a key, but no value found")
        return valdict

