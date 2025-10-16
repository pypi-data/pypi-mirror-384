## Welcome!

This package will help you manage Pipelines and your AWS infrastructure with the power of CDK!

## How credentials are pulled

This package is configured to load both Isengard and Conduit CDK plugins when running the CDK
Toolkit. These plugins automatically fetch the credentials from the brokers for each account
during deployment. In most cases, you only need one of them. Consider removing
the plugin that you don't need. For more information see their READMEs:

- https://code.amazon.com/packages/Aws-cdk-isengard-plugin
- https://code.amazon.com/packages/Aws-cdk-conduit-plugin

## Operating this package

Out of the box, this package provides two npm scripts for `cdk` and `amzn-cdk` commands, which you can run with `brazil-build` or `npm` directly. For example:

```
brazil-build run cdk deploy <StackName>
brazil-build run amzn-cdk deploy:pipeline
```

They are the AWS CDK Toolkit and the internal command-line tool that helps to bootstrap
and deploy your internal pipelines, respectively.

To understand what those commands offer, see the documentation of the [`amzn-cdk` command](https://code.amazon.com/packages/AmznCdkCli/blobs/mainline/--/README.md)
and [`cdk` command](https://docs.aws.amazon.com/cdk/v2/guide/cli.html).

## Local Development

1. Clone the repository

2. Go to **src/streamlit_app** folder

```bash
cd src/streamlit_app
```

3. Install the required packages using venv:

```bash
python3 -m venv env
source env/bin/activate
pip install -r requirements.txt
```

4. Execute it using streamlit

```
cd src
streamlit run main.py
```

5. You can then update the main.py file to add new business logics

## Notes about bootstrapping

Upon cloning, this package does not contain any deployment target, thus it has nothing to bootstrap. The command
`amzn-cdk bootstrap` would fail until you [expand your pipeline](https://builderhub.corp.amazon.com/docs/native-aws/developer-guide/cdk-howto-expand-pipeline.html).

## Other useful links:

- [NativeAWS's how-to guides](https://builderhub.corp.amazon.com/docs/native-aws/developer-guide/)
- [Pipelines constructs references](https://code.amazon.com/packages/PipelinesConstructs/blobs/mainline/--/README.md)
- [CDK constructs references](https://docs.aws.amazon.com/cdk/api/latest/versions.html)
- [Catalogue of CDK libraries](https://builderhub.corp.amazon.com/docs/native-aws/developer-guide/cdk-construct-libraries.html)
