# EASYSSL 

EasySSL helps you to generate SSL certificates chains.

EasySSL follows Openssl standards and configurations. Visit this site for more information :
[Openssl Documentation](https://jamielinux.com/docs/openssl-certificate-authority/create-the-root-pair.html)

## Requirements

* All : `OpenSSL 1.1.1`
* `platform.py`feature : 
    * python >= `3.8`
    * `pyyaml` module
    
## Getting started

Generate certificate chains :

```sh
./easyssl.sh -h
```

Generate stores from existing certificates :

```sh
./bin/store.sh -h
```