# IronSafe: A Secure and Policy-Compliant Query Processing Architecture

Computation Storage Architectures (CSA) are increasingly adopted in the cloud for near data processing, where the underlying storage devices/servers are now equipped with heterogeneous cores which enable computation offloading near to the data. While CSA is a promising high-performance architecture for the cloud, in general data analytics also presents significant data security and policy compliance (e.g., GDPR) challenges in untrusted cloud environments.
 
In this work, we present IronSafe, a secure and policy-compliant query processing system for heterogeneous computational storage architectures, while preserving the performance advantages of CSA in untrusted cloud environments. To achieve these design properties in a computing environment with heterogeneous host (x86) and storage system (ARM), we design and implement the entire hardware and software system stack from the ground-up leveraging hardware-assisted Trusted Execution Environments (TEEs): namely, Intel SGX and ARM TrustZone. More specifically, IronSafe builds on three core contributions: (1) a heterogeneous confidential computing framework for shielded execution with x86 and ARM TEEs and associated secure storage system for the untrusted storage medium; (2) a policy compliance monitor to provide a unified service for attestation and policy compliance; and (3) a declarative policy language and associated interpreter for concisely specifying and efficiently evaluating a rich set of polices. Our evaluation using the TPC-H SQL benchmark queries and GDPR anti-pattern use-cases shows that IronSafe is faster, on average by 2.3× than a host-only secure system, while providing strong security and policy-compliance properties.

# Reproducing results in the paper

IronSafe was published in SIGMOD '22. To reproduce the evaluation results shown in the paper take a look at the [evaluation README](./evaluation.md).

# Referencing our work

Coming soon.
