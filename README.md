# EASYSSL 

Create in one short command : 

* `platform` certificates and stores for hosts connected with each other
* `chain` of certificates for a single host
* `store` from certificates

## Getting started

```sh
./install.sh
# main features
eayssl -h
```

Try in a terminal:

```sh
# All the TLS material for 3 connected hosts with various users
easyssl platform --conf easyssl/resources/conf/platform_conf_example.yml

# A chain of certificates for a host named 'node01'
easyssl chain --server --san node01
easyssl chain --extract ~/mychains

# A keystore and the related trustsore from existing keys and certs
easyssl store --key ~/mykey.p8 --cert ~/mycert.crt --cacert ~/myca_file.crt --pass secret
```

Learn more about extended usages :

```sh
eayssl platform -h
eayssl chain -h
eayssl store -h
```

Just play with it !

## Requirements

| Feature  | Requirements                                          |
|----------|-------------------------------------------------------|
| chain    | openssl 1.1.1                                         |
| store    | openssl 1.1.1<br>java >= 1.8<br>keytool               |
| platform | openssl 1.1.1<br>java >= 1.8<br>keytool<br>python 3.8 |
