# ca_certs.pem
The provided `ca_certs.pem` is comprised of CA certs from:
* Internet Security Research Group (ISRG)
* InCommon (RSA and IGTF)

### ISRG
ISRG signs certs for Let'sEncrypt, which is used by the AMQP server, so these certs
are required in order to connect to the AMQP server for publishing data.
Let'sEncrypt is also the most common signing authority in use.
Root certs are from: https://letsencrypt.org/certificates/


### InCommon
InCommon is the second most common signing authority among educational institutions.
Root certs are from: https://dist.igtf.net/distribution/current/


# Adding root certs from other CAs
The default `ca_certs.pem` might need to be updated (rare) if:
* You are authenticating to the AMQP server using signed certs (instead of
  username/password combo)
* Your certs are issued from a CA other than Let'sEncrypt or InCommon

If all of the above are true, you should get the appropriate CA cert in PEM format
and *append* it to `ca_certs.pem` by running:
```bash
bash mk_ca_certs.sh
```
and answering the prompts as follows:
* Make new ca_certs.pem?
  * NO
* Choose pem file to include ...
  * Enter the number of the new cert to include
  * Repeat for each new cert you have to add
  * Choose 'quit' (option 1) when you have selected all the new certs to add
