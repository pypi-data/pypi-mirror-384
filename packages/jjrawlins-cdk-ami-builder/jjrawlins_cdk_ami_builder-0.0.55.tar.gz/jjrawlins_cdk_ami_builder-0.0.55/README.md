# ImagePipeline Construct for AWS CDK

## Overview

The `ImagePipeline` construct is a versatile and powerful component of the AWS Cloud Development Kit (CDK) designed for
creating and managing AWS Image Builder pipelines. This construct simplifies the process of setting up automated
pipelines for building and maintaining Amazon Machine Images (AMIs). It provides extensive customization options,
enabling users to tailor the pipeline to specific needs, including vulnerability scanning, cross-account distribution,
and more.

## Benefits

1. **Customizable Image Building**: Offers a wide range of parameters to customize the AMI, including VPC settings,
   security groups, instance types, and more.
2. **Automated Pipeline Management**: Automates the pipeline creation and execution process, reducing manual effort and
   potential errors.
3. **Cross-Account AMI Distribution**: Facilitates the copying of AMIs to multiple AWS accounts, enhancing resource
   sharing and collaboration.
4. **Vulnerability Scanning Integration**: Supports integration with AWS Inspector for continuous vulnerability
   scanning, ensuring security compliance.
5. **User-Friendly**: Designed with user experience in mind, making it easy to integrate into AWS CDK projects.
6. **Scalability and Flexibility**: Scales according to your needs and provides flexibility in configuring various
   aspects of the image building process.

## Prerequisites

* AWS account and AWS CLI configured.
* Familiarity with AWS CDK and TypeScript.
* Node.js and npm installed.

## Installation

Ensure that you have the AWS CDK installed. If not, you can install it using npm:

```bash
npm install -g aws-cdk
```

Next, add the `ImagePipeline` construct to your CDK project:

```bash
npm install '@jjrawlins/cdk-ami-builder' --save
```

## Usage Example

Below is an example of how to use the `ImagePipeline` construct in your CDK application.

### Importing the Construct

First, import the `ImagePipeline` construct into your CDK application:

```python
import { ImagePipeline } from '@jjrawlins/cdk-ami-builder';
```

### Using the Construct

Here's an example of how to use the `ImagePipeline` construct:

```python
const vpc = new Vpc(this, 'Vpc', {
    ipAddresses: IpAddresses.cidr(props.vpcCidr as string),
    maxAzs: 2,
    subnetConfiguration: [
        {
            name: 'Public',
            subnetType: SubnetType.PUBLIC,
            cidrMask: 24,
        },
        {
            name: 'Private',
            subnetType: SubnetType.PRIVATE_WITH_EGRESS,
            cidrMask: 24,
        },
    ],
    natGateways: 1,
});

const image = ec2.MachineImage.lookup({
    name: 'ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*',
    owners: ['099720109477'],
});

const version = process.env.IMAGE_VERSION_NUMBER ?? '0.0.8';

const imagePipeline = new ImagePipeline(this, 'ImagePipeline', {
    parentImage: image.getImage(this).imageId,
    vpc: vpc,
    imageRecipeVersion: version,
    components: [
        {
            name: 'Install-Monitoring',
            platform: 'Linux',
            componentDocument: {
                phases: [{
                    name: 'build',
                    steps: [
                        {
                            name: 'Install-CloudWatch-Agent',
                            action: 'ExecuteBash',
                            inputs: {
                                commands: [
                                    'apt-get update',
                                    'DEBIAN_FRONTEND=noninteractive apt-get install -y g++ make cmake unzip libcur14-openssl-dev',
                                    'DEBIAN_FRONTEND=noninteractive apt-get install -y curl sudo jq bash zip unzip iptables software-properties-common ca-certificates',
                                    'curl -sfLo /tmp/amazon-cloudwatch-agent.deb https://s3.amazonaws.com/amazoncloudwatch-agent/ubuntu/amd64/latest/amazon-cloudwatch-agent.deb',
                                    'dpkg -i -E /tmp/amazon-cloudwatch-agent.deb',
                                    'rm /tmp/amazon-cloudwatch-agent.deb',
                                ],
                            },
                        },
                    ],
                }],
            },
        },
    ],
});

new CfnOutput(this, `ImageId-${this.stackName}`, {
    value: imagePipeline.imageId,  // Only valid if autoBuild=true
    description: 'The AMI ID of the image created by the pipeline',
});
```

This example demonstrates creating a new VPC and setting up an Image Pipeline within it. You can customize the `

ImagePipeline` properties according to your requirements.

### Customization Options

* `vpc`: Specify the VPC where the Image Pipeline will be deployed.
* `parentImage`: Define the base AMI for the image recipe.
* `components`: List custom components for the AMI, such as software installations and configurations.
* Additional properties like `imageRecipeVersion`, `platform`, `enableVulnScans`, etc., allow further customization.

### Outputs

The construct provides outputs like `imagePipelineArn` and `imageId`, which can be used in other parts of your AWS
infrastructure setup.

## Best Practices

1. **Parameter Validation**: Ensure that all inputs to the construct are validated.
2. **Security**: Follow best practices for security group and IAM role configurations.
3. **Resource Naming**: Use meaningful names for resources for better manageability.
4. **Error Handling**: Implement error handling for pipeline execution and custom resources.

## Support and Contribution

For support, please contact the package maintainer or open an issue in the repository. Contributions to the package are
welcome. Please follow the contribution guidelines in the repository.

---


This README provides a basic guide to getting started with the `ImagePipeline` construct. For more advanced usage and
customization, refer to the detailed documentation in the package.

![User](https://lh3.googleusercontent.com/a/AEdFTp6yNsN1-EC5-OZ2vss91NDDYmHKgEHn8xwdd6eS=s96-c)
