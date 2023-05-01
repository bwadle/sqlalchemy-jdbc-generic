# sqlajdbc.py
# This module is released as-is without warranty under AT&T BSD Liscense.
# see liscense.md

'''
SQLAlchemy Dialect intended to provide a minimume viable JDBC driver based
implementation of SQLAlchemy connection interactions based on the 
JayDeBeApi module.

JayDeBeApi https://github.com/baztian/jaydebeapi
SQLAlchemy https://www.sqlalchemy.org/
'''

from sqlalchemy.engine import default
import jaydebeapi as jaydebeapi_ext
from urllib.parse import quote_plus, unquote

''' 
Modify how the base jaydebeapi interacts with jpype and add hooks to 
allow passing of JVM initial arguments.
'''

def _jdbc_connect_jpype(jclassname, url, driver_args, jars, libs, *args, **kwargs):
    """ from jaydebeapi: modified to allow passthrough arguments """
    import jpype
    from os import path as osp
    from re import match
    if not jpype.isJVMStarted():
        args = list(args)
        class_path = []
        if jars:
            class_path.extend(jars)
        class_path.extend(jaydebeapi_ext._get_classpath())
        if class_path:
            args.append('-Djava.class.path=%s' %
                        osp.pathsep.join(class_path))
        if libs:
            # path to shared libraries
            libs_path = osp.pathsep.join(libs)
            args.append('-Djava.library.path=%s' % libs_path)
        if '_jvmargs' in kwargs.keys():
            args.append(kwargs['_jvmargs'])
        jvmpath = kwargs.get(
            "_jvmpath", 
            jpype.getDefaultJVMPath()
            )
        if hasattr(jpype, '__version__'):
            try:
                ver_match = match('\d+\.\d+', jpype.__version__)
                if ver_match:
                    jpype_ver = float(ver_match.group(0))
                    if jpype_ver < 0.7:
                        jaydebeapi_ext.old_jpype = True
            except ValueError:
                pass
        if jaydebeapi_ext.old_jpype:
            jpype.startJVM(jvmpath, *args)
        else:
            jpype.startJVM(jvmpath, *args, ignoreUnrecognized=True,
                           convertStrings=True)
    if not jpype.isThreadAttachedToJVM():
        jpype.attachThreadToJVM()
        jpype.java.lang.Thread.currentThread().setContextClassLoader(jpype.java.lang.ClassLoader.getSystemClassLoader())
    if jaydebeapi_ext._jdbc_name_to_const is None:
        types = jpype.java.sql.Types
        types_map = {}
        if jaydebeapi_ext.old_jpype:
          for i in types.__javaclass__.getClassFields():
            const = i.getStaticAttribute()
            types_map[i.getName()] = const
        else:
          for i in types.class_.getFields():
            if jpype.java.lang.reflect.Modifier.isStatic(i.getModifiers()):
              const = i.get(None)
              types_map[i.getName()] = const 
        jaydebeapi_ext._init_types(types_map)
    if jaydebeapi_ext._java_array_byte is None:
        def _java_array_byte(data):
            return jpype.JArray(jpype.JByte, 1)(data)
    # register driver for DriverManager
    jpype.JClass(jclassname)
    if isinstance(driver_args, dict):
        Properties = jpype.java.util.Properties
        info = Properties()
        for k, v in driver_args.items():
            info.setProperty(k, v)
        dargs = [ info ]
    else:
        dargs = driver_args
    return jpype.java.sql.DriverManager.getConnection(url, *dargs)

jaydebeapi_ext._jdbc_connect = _jdbc_connect_jpype

# DB-API 2.0 Module Interface connect constructor
def connect(_class, url, _dargs=None, _jars=None, _libs=None, *args, **kwargs):
    """ from jaydebeapi: modified to allow passthrough of arguments """
    if isinstance(_dargs, jaydebeapi_ext.string_type):
        _dargs = [ _dargs ]
    if not _dargs:
       _dargs = []
    if _jars:
        if isinstance(_jars, jaydebeapi_ext.string_type):
            _jars = [ _jars ]
    else:
        _jars = []
    if _libs:
        if isinstance(_libs, jaydebeapi_ext.string_type):
            _libs = [ _libs ]
    else:
        _libs = []
    jconn = jaydebeapi_ext._jdbc_connect(_class, url, _dargs, _jars, _libs, *args, **kwargs)
    return jaydebeapi_ext.Connection(jconn, jaydebeapi_ext._converters)

jaydebeapi_ext.connect = connect


class BaseJDBCDialect(default.DefaultDialect):
    ''' Base JDBC dialect '''

    name = 'sqlajdbc'
    driver = 'jaydebeapi_ext'

    @classmethod
    def dbapi(cls):
        return jaydebeapi_ext

    def create_connect_args(self, url):
        '''
        Parse jdbc connection string with optional JayDeBeApi arguments
        pick up optional jaydebeapi keyword arguments if supplied.

        JayDeBeAPI's connection parameters need to be parsed from the 
        connection url provided when using this dialect.

        JayDeBeApi_ext connect method parameters:
            jclassname (required): The Java class entrypoint for the JDBC driver
            url (required): Database url as would be given as a jdbc connection string
            driver_args: dict of arguments to pass to jaydebeapi.connect()
            jars: path to jar file or list of jar paths
            libs: DLL filenames to pass to JDBC driver 

        Typical url parameter supplied would include the sqlalchemy dialect followed by 
        a jdbc connection string less the jdbc:driver:// declaration.  The connection type
        is always assumed to be jdbc and the driver name should be supplied within the url using
        jclass=driver. 
        
        For Example

        ::
        
            jdriver = 'drivername'
            jclass = 'org.jdbc.driverclass'
            jars = '/path/to/driver.jar'
            host = 'mydb.server.net'

            eng = create_engine(
                f'sqlajdbc://{host}?jdriver={jdriver}&jclass={jclass}&jars={jars}'
                )    
        '''
        jdbc_kw = [
            '_class',
            '_driver',
            '_dargs',
            '_jars',
            '_libs',
            '_jvmpath',
            '_jvmargs'
        ]
        jdbc_qformat_kw = [
            '_start',
            '_assoc',
            '_sep',
            '_end',
            '_raw_host'
            ]
        orig_opts = url.translate_connect_args()
        
        orig_opts.update(url.query)
        new_opts = {}
        
        
        _start = unquote(orig_opts.pop('_start', '?'))
        _sep = unquote(orig_opts.pop('_sep', '&'))
        _assoc = unquote(orig_opts.pop('_assoc', '='))
        _end = unquote(orig_opts.pop('_end', ''))
        _raw_host = bool(orig_opts.pop('_raw_host', False))

        host = orig_opts.pop("host")
        if _raw_host:
            host = str(url).split(_start)[0]
            host = host.split('://')[-1]
        host_agg = host

        for k,v in orig_opts.items():
            if k in jdbc_kw:
                new_opts[k] = v
            elif k in jdbc_qformat_kw:
                continue
            else:
                pre = _start if host == host_agg else _sep
                host += f'{pre}{k}{_assoc}{quote_plus(str(v))}'
        host += _end

        if '_jars' in new_opts.keys():
            new_opts['_jars'] = unquote(new_opts['_jars']).split(',')
        new_opts['url'] = unquote(f'jdbc:{new_opts.pop("_driver")}://{host}')

        return [[], new_opts]

dialect = BaseJDBCDialect