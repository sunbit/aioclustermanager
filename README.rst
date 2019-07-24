Introduction
============

An asyncio library to manage orchestrators with support for Kubernetes and Nomad.


Quickstart
----------

We use context managers with a configuration object::

    config_k8s = {
        'certificate': '<client certificate data>',
        'key': '<client key data>',
        'endpoint': 'localhost:6443',
        'skip_ssl': True
    }
    async with K8SContextManager(k8s_config) as context:
          cm = ClusterManager(context)
          await cm.delete_namespace('aiocluster-test')
          await cm.create_namespace('aiocluster-test')

Auth
----

Inside cluster Auth (Pod token)
===============================

Configuration::

    config_k8s = {
      'auth': 'in_cluster'
    }


Token is gotten from env var `KUBERNETES_SERVICE_TOKEN` or `/var/run/secrets/kubernetes.io/serviceaccount/token`

Ca is gotten from `/var/run/secrets/kubernetes.io/serviceaccount/ca.crt`

Certificate BASE64
==================

Configuration::

    config_k8s = {
      'auth': 'certificate',
      'certificate': 'BASE64_CERT',
      'key': 'BASE64_KEY'
    }


Certificate Files
=================

Configuration::

    config_k8s = {
      'auth': 'certificate_file',
      'certificate': 'CERT_PEM_FILE',
      'key': 'KEY_PEM_FILE'
    }

Key is optional if certificate has a chain with the key


Basic Auth
==========

Configuration::

    config_k8s = {
      'auth': 'basic_auth',
      'user': 'USERNAME',
      'credentials': 'PASSWORD'
    }


Token Auth
==========

Configuration::

    config_k8s = {
      'auth': 'token',
      'token': 'JWT_TOKEN_BASE_64',
    }


Connection
----------

Scheme, host and port
=====================

Configuration::

    config_k8s = {
      'http_scheme': 'SCHEME',  # http/https Default: 'http'
      'endpoint': 'HOST:PORT',
    }

HTTPS certificate validation
============================

You can skip validation::

    config_k8s = {
      'skip_ssl': 'false',  # 'false'/'true' Default: 'false'
    }

You can define BASE64 CA certificate::

    config_k8s = {
      'ca': 'BASE64_CA_CERT'
    }


You can define CA certificate file::

    config_k8s = {
      'ca_file': 'CERT_PEM_FILE'
    }

In case its in_cluster auth the certificate is gotten from by default from `/var/run/secrets/kubernetes.io/serviceaccount/ca.crt`. Can be overwritten defining your own.

Configure Cluster auth
----------------------

In order to use token based auth you can define a service account on the cluster that has role based permissions to do the operations that you need.

Create serviceaccount::

  $ kubectl create serviceaccount myuser -n namespace

Get token::

  $ kubectl get serviceaccounts myuser -o yaml -n namespace
  apiVersion: v1
  kind: ServiceAccount
  metadata:
    # ...
  secrets:
  - name: myuser-token-1yvwg
  $ kubectl get secret myuser-token-1yvwg -o yaml -n namespace
  apiVersion: v1
  data:
    ca.crt: (APISERVER'S CA BASE64 ENCODED)
    namespace: ZGVmYXVsdA==
    token: (BEARER TOKEN BASE64 ENCODED)
  kind: Secret
  metadata:
    # ...
  type: kubernetes.io/service-account-token


Add roles to the service account::

  kubectl create clusterrolebinding myuser-job-controller --clusterrole=system:controller:job-controller --user=myuser

To Run Tests
------------

Nomad:

You can download the nomad agent and run it with:

    nomad agent -dev

Tests will connect to the local nomad to schedule the jobs

K8S:

Tests will check if there is a k8s context names docker-desktop or minikube