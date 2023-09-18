# -*- encoding: utf-8 -*-
# requires a recent enough python with idna support in socket
# pyopenssl, cryptography and idna

from datetime import datetime, timedelta
from OpenSSL import SSL
from cryptography import x509
from cryptography.x509.oid import NameOID
import idna
import pandas as pd
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)
from socket import socket
from collections import namedtuple

HostInfo = namedtuple(field_names='cert hostname peername', typename='HostInfo')

HOSTS = [
    ('topresume.com', 443),('talentinc.com', 443),('topcv.com', 443),('topcv.co.uk', 443),('resume.io', 443),('career.io', 443),('careerminds.com', 443)   
]

f = open("test.txt", "r")



def get_certificate(hostname, port):
    hostname_idna = idna.encode(hostname)
    sock = socket()
    try:
        sock.connect((hostname, port))
        peername = sock.getpeername()
        ctx = SSL.Context(SSL.SSLv23_METHOD) # most compatible
        ctx.check_hostname = False
        ctx.verify_mode = SSL.VERIFY_NONE

        sock_ssl = SSL.Connection(ctx, sock)
        sock_ssl.set_connect_state()
        sock_ssl.set_tlsext_host_name(hostname_idna)
        sock_ssl.do_handshake()
        cert = sock_ssl.get_peer_certificate()
        crypto_cert = cert.to_cryptography()
        sock_ssl.close()
        sock.close()
        return HostInfo(cert=crypto_cert, peername=peername, hostname=hostname)
    except:
        print("domain not servalble in port 443")

    return None


import concurrent.futures
if __name__ == '__main__':
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as e:
        format = '%Y-%d-%m %H:%M:%S'
        expiring_hosts = list()
        df = pd.DataFrame(columns = ['Domain Name', 'Expiring in next 30 days', 'Expiring Date'])
        td_date = datetime.strptime( str(datetime.now().strftime(format)) , format)
        for domain in f:
            domain = domain.strip()[:-1]
            if domain.startswith('\\') or domain.startswith('_') or domain.find('_') != -1:
                print("not valid domain", domain)    
            else:
                print(domain)
                result=get_certificate(domain, port=443)
                if result == None:
                    print("Skipping domain",domain)
                else:
                    try: 
                        for hostinfo in result:
                            if hostinfo.cert.not_valid_after < td_date+timedelta(days=30):
                                df = df.append({'Domain Name' : hostinfo.hostname, 'Expiring in next 30 days' : 'Yes', 'Expiring Date' : hostinfo.cert.not_valid_after },ignore_index = True)
                            else :
                                df = df.append({'Domain Name' : hostinfo.hostname, 'Expiring in next 30 days' : 'No', 'Expiring Date' : hostinfo.cert.not_valid_after },ignore_index = True)
                    except :
                        print("error",domain)
        print(df)