# TODO

* '--keypass' option
    * encrypt the node key with password
* 'setup.sh'
    * Move the configuration and templating steps into this shell script

## In progress

## Done

* '--san' option
    * Add SAN to the generated cert
    * accept DNS and IP entries
* '--issuer' option
    * Provide a path to an issuer folder
    * all the generated certs are signed by this issuer
* '--name' option
    * override the CN of the certificates
    * override the chain name, the folders name and the keys and certs names
* Keystore generation
* Truststore generation