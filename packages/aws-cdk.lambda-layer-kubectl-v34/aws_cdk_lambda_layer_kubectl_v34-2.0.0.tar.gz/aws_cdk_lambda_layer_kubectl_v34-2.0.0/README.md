# Lambda Layer with KubeCtl v1.34

<!--BEGIN STABILITY BANNER-->---


![cdk-constructs: Stable](https://img.shields.io/badge/cdk--constructs-stable-success.svg?style=for-the-badge)

---
<!--END STABILITY BANNER-->

This module exports a single class called `KubectlV34Layer` which is a `lambda.LayerVersion` that
bundles the [`kubectl`](https://kubernetes.io/docs/reference/kubectl/kubectl/) and the
[`helm`](https://helm.sh/) command line.

> * Helm Version: 3.19.0
> * Kubectl Version: 1.34.0

Usage:

```python
// KubectlLayer bundles the 'kubectl' and 'helm' command lines
import { KubectlV34Layer } from '@aws-cdk/lambda-layer-kubectl-v32';
import * as lambda from 'aws-cdk-lib/aws-lambda';

declare const fn: lambda.Function;
const kubectl = new KubectlV34Layer(this, 'KubectlLayer');
fn.addLayers(kubectl);
```

`kubectl` will be installed under `/opt/kubectl/kubectl`, and `helm` will be installed under `/opt/helm/helm`.
