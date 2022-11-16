# EASYCA

All the certificates you want in one short command !

## Requirements

| Package | Version   |
|---------|-----------|
| Openssl | >= 1.1.1f |
| Python  | >= 3.10   |

## Install

```sh
./install.sh
```

## Quick Start

```sh
easyca create certs --config conf_example
easyca export certs --output $HOME
```

## Configuration

| Configuration | Mandatory | Type   | Default     | Description                                            |
|---------------|-----------|--------|-------------|--------------------------------------------------------|
| version       | Yes       | String | None        | easyca version                                         |
| certs[].cn    | Yes       | String | None        | Certificate CN value                                   |
| certs[].san   | No        | String | "127.0.0.1" | Certificate SAN value. Format is `"ip1,name1,ip2,ip3"` |
