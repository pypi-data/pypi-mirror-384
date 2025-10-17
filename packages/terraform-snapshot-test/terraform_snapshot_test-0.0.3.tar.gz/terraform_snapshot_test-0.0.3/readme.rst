*************************************
Terraform / OpenTofu Snapshot Testing
*************************************

Testing Terraform and OpenTofu code is difficult. The typical approach requires deploying infrastructure to verify correctness, which is slow, expensive, and blocks other developers. Native Terraform testing tools either require spinning up real resources or are limited in what they can validate.

This library provides snapshot testing for Terraform and OpenTofu modules. It generates and compares JSON snapshots of your planned infrastructure changes without deploying anything. Tests run using read-only credentials against provider APIs, giving you fast feedback on whether your code produces the infrastructure you expect.

`GitHub project home <https://github.com/joaorodrig/terraform-snapshot-test>`_

Table of Contents
-----------------

.. contents::
    :backlinks: none



Terraform / OpenTofu Unit Testing is complex and brittle
--------------------------------------------------------

Following `Martin Fowler's The Practical Test Pyramid <https://martinfowler.com/articles/practical-test-pyramid.html>`_, unit tests should be fast, numerous, and cheap to run. Traditional Terraform testing does not allow for rapid and cheap iterations when developing complex infrastructure.

**Current approaches are problematic:**

- Native Terraform tests require deploying real infrastructure, making them slow and costly;
- Manual plan reviews catch issues late and don't prevent regressions;
- No tests at all means finding problems only after deployment to non-prod or production environments;

**This creates practical issues:**

- Developers wait minutes or hours for feedback on their changes;
- Testing blocks access to shared state files, preventing parallel development;
- Infrastructure changes risk unexpected modifications without pre-deployment verification;
- Teams spend significant time and money deploying test infrastructure just to validate code;

Snapshot Testing of Terraform / OpenTofu as Unit Testing
--------------------------------------------------------

This library treats Terraform plans as unit test artifacts. You create test stacks that exercise your modules with different configurations, generate snapshots of the planned changes, and commit those snapshots to version control.

On every commit, the test suite verifies that your code still produces the expected plan. Changes to the planned infrastructure surface immediately in code review as snapshot diffs, making unintended consequences visible before any deployment.

This does not replace deployment testing in non-production environments. You still need to deploy and validate that your infrastructure actually works. Snapshot testing happens before deployment, catching problems earlier and more frequently:

- Run snapshot tests on every commit (seconds);
- Deploy to non-prod environment (minutes to hours);
- Run integration tests and validate behavior;
- Deploy to production;

The value is in the feedback loop. Snapshot tests catch configuration errors, unintended resource changes, and broken module logic immediately—problems that would otherwise only surface after waiting for a deployment. This means fewer failed deployments, faster iteration, and earlier detection of regressions.

Tests run in seconds using only read-only provider credentials. No state files, no deployed resources, no waiting.

You can find this library in this `pypi repository <https://pypi.org/project/terraform-snapshot-test>`_.

Implementation
--------------

This module introduces the concept of Terraform snapshot unit testing. Testing your code can give you faster feedback cycles and guard you against unwanted changes. Snapshot tests are useful when you want to make sure your infrastructure does not change unexpectedly.

This approach still needs to be discussed as part of the wider team, but here's how it works:

#. You work on the Terraform module as usual. In the ``tests/`` folder within the module, you create one or more test stacks which will produce different desired instantiations of the module. Once you're happy witht the module and test instances, you then generate the snapshot using the ``pytest -m terraform --snapshot-update -s`` command;
#. This will then intialise the Terraform modules, and use read-only credentials to the software provider (e.g `AWS <https://github.com/joaorodrig/terraform-snapshot-test/tests/aws-s3-bucket>`_, `GitLab <https://github.com/joaorodrig/terraform-snapshot-test/tests/gitlab-project>`_, `GitHub <https://github.com/joaorodrig/terraform-snapshot-test/tests/github-repository>`_) to create a test plan. The synthetesis and planned values of the plan are then persisted as a snapshot of the test, without touching any infrastructure or state;
#. You can visually inspect the generated manifests and plans in json, to verify that certain code conditions and resources exist in the way intended by the developer. In future releases, this verification will be done programatically using `Syrupy <https://syrupy-project.github.io/syrupy/>`_ and customisable YAML (e.g. verify that a specific object type with specific settings exists in a specific Terraform address);
#. This snapshot testing can be executed at every push, to ensure that the intent of the developer is explictly captured in the test;

Advantages
==========

**Fast feedback cycles:**

- Tests run in seconds, not minutes or hours;
- Developers get immediate feedback on code changes;
- No waiting for infrastructure deployment or destruction;

**No infrastructure costs:**

- Uses read-only provider credentials for planning only;
- No actual resources created during testing;
- No state files to manage or clean up;

**Prevents unintended changes:**

- Snapshot diffs make all infrastructure changes explicit;
- Unexpected modifications surface immediately in code review;
- Guards against regressions when refactoring modules;

**Enables parallel development:**

- No shared state file contention between developers;
- Multiple team members can test simultaneously;
- No blocking on deployment environments;

**Encourages better module design:**

- Forces developers to write truly modular, reusable code;
- Modules must accept configuration through variables which may be static or dynamic references;
- Dependencies can be injected or coupled to remote state, depending on use-case;
- Results in cleaner, more maintainable infrastructure code;

**Integrates with existing workflows:**

- Runs as part of standard CI/CD pipelines;
- Uses familiar pytest framework and conventions;
- Snapshot diffs appear in pull request reviews like any other code change;

**Complements deployment testing:**

- Catches configuration errors before expensive deployments;
- Reduces failed deployment attempts;
- Narrows the scope of issues found in non-prod environments;

Limitations
===========

**Cannot test composed infrastructure**

- Snapshot testing works well for isolated modules;
- Testing multiple stacks that reference each other's outputs is difficult;
- Cross-stack dependencies require remote state, which this approach bypasses;
- Complex multi-stack compositions still need integration testing via deployment;

**Limited to plan validation:**

- Only validates what Terraform intends to create;
- Cannot verify that infrastructure actually works as expected;
- Does not catch provider-specific issues or API behavior;
- Cannot test runtime behavior or integration between services;

**Requires disciplined module design:**

- Modules must be written with dependency injection in mind;
- Tightly coupled modules cannot be tested in isolation;
- Teams need to adopt modular patterns consistently;

**Snapshot maintenance overhead:**

- Snapshots must be updated when intentional changes occur;
- Reviewing snapshot diffs requires understanding Terraform plan JSON;
- False positives from provider version updates or irrelevant changes;

**Does not replace other testing:**

- Still need deployment to non-prod for integration testing;
- Still need manual verification of deployed infrastructure;
- Still need production-like testing for performance and reliability;
- This is one layer in a comprehensive testing strategy, not the entire strategy;

**Limited programmatic validation:**

- Current implementation focuses on snapshot comparison;
- Verifying specific resource configurations requires manual inspection;
- Automated assertion of specific properties is planned but not yet implemented;
- Cannot easily test conditional logic or complex module behavior;


Usage
-----

Simple Example
==============

#. In the root folder of the Terraform / OpenTofu module, create a ``pytest.ini`` and customise environment variables based on your use-case and CI job (`AWS example <https://github.com/joaorodrig/terraform-snapshot-test/blob/main/examples/aws-s3-bucket/pytest.ini>`_ below):

    ::

        [pytest]
        markers =
            terraform: test Terraform / Tofu code
            order: order the tests
        addopts = --snapshot-warn-unused
        pythonpath = .
        env =
            TF_TEST_CMD=tofu
            AWS_DEFAULT_REGION=eu-west-1
            ADDITIONAL_TF_OVERRIDE_LOCATIONS=../

#. Create a ``tests`` folder in the Terraform / OpenTofu module, and copy (or link if in composed repository) the test helpers (`AWS tests example <https://github.com/joaorodrig/terraform-snapshot-test/tree/main/examples/aws-s3-bucket/tests>`_ below):

    ::

        mkdir tests/
        cd tests/
        ln -s ../../../etc/tests-helpers/* .

#. Overwrite your software providers (`AWS provider example <https://github.com/joaorodrig/terraform-snapshot-test/blob/main/examples/aws-s3-bucket/tests/provider.tf>`_) to prevent interaction with the state backend, and create the test stack with the instantiations needed (AWS  test stack example);

    ::

        # Go back to the Terraform / OpenTofu module root
        cd ..

        # Install the environment
        python3.12 -m venv .venv
        source .venv/bin/activate
        pip install -r tests/requirements-test.txt

#. After making changes to you your module and reflecting these in the test instances, generate the snapshot:

    ::

        pytest -m terraform --snapshot-update -s

#. This is an example of the expected output:

    ::

        ============================================================== test session starts ===============================================================
        platform linux -- Python 3.12.3, pytest-8.4.2, pluggy-1.6.0
        rootdir: /home/user/workspace/github/terraform-snapshot-test/tests/aws-s3-bucket
        configfile: pytest.ini
        plugins: syrupy-5.0.0, order-1.3.0, env-1.1.5
        collected 2 items

        tests/test_terraform_snapshot.py
        Initializing the backend...
        Initializing modules...

        Initializing provider plugins...
        - terraform.io/builtin/terraform is built in to OpenTofu
        - Reusing previous version of hashicorp/aws from the dependency lock file
        - Using previously-installed hashicorp/aws v6.15.0

        ╷
        │ Warning: Backend configuration ignored
        │
        │   on ../config.tf line 2, in terraform:
        │    2:   backend "s3" {}
        │
        │ Any selected backend applies to the entire configuration, so OpenTofu expects provider configurations only in the root module.
        │
        │ This is a warning rather than an error because it's sometimes convenient to temporarily call a root module as a child module for testing
        │ purposes, but this backend configuration block will have no effect.
        │
        │ (and one more similar warning elsewhere)
        ╵

        OpenTofu has been successfully initialized!

        You may now begin working with OpenTofu. Try running "tofu plan" to see
        any changes that are required for your infrastructure. All OpenTofu commands
        should now work.

        If you ever set or change modules or backend configuration for OpenTofu,
        rerun this command to reinitialize your working directory. If you forget, other
        commands will detect it and remind you to do so if necessary.
        ╷
        │ Warning: Backend configuration ignored
        │
        │   on ../config.tf line 2, in terraform:
        │    2:   backend "s3" {}
        │
        │ Any selected backend applies to the entire configuration, so OpenTofu expects provider configurations only in the root module.
        │
        │ This is a warning rather than an error because it's sometimes convenient to temporarily call a root module as a child module for testing
        │ purposes, but this backend configuration block will have no effect.
        ╵
        Success! The configuration is valid, but there were some validation warnings as shown above.
        module.stack_test_static_variable.data.aws_caller_identity.deployment_account: Reading...
        module.stack_test_static_variable.data.aws_caller_identity.deployment_account: Read complete after 0s [id=188415274210]
        module.stack_test_static_variable.data.aws_caller_identity.target_account: Reading...
        module.stack_test_static_variable.data.aws_caller_identity.target_account: Read complete after 0s [id=188415274210]

        OpenTofu used the selected providers to generate the following execution plan. Resource actions are indicated with the following symbols:
        + create
        <= read (data resources)

        OpenTofu will perform the following actions:

        # module.stack_test_static_variable.data.aws_iam_policy_document.storage will be read during apply
        # (config refers to values not yet known)
        <= data "aws_iam_policy_document" "storage" {
            + id            = (known after apply)
            + json          = (known after apply)
            + minified_json = (known after apply)

            + statement {
                + actions   = [
                    + "s3:GetObject",
                    + "s3:ListBucket",
                    ]
                + resources = [
                    + (known after apply),
                    + (known after apply),
                    ]

                + principals {
                    + identifiers = [
                        + "arn:aws:iam::111111111111:role/lucille",
                        ]
                    + type        = "AWS"
                    }
                }
            }

        # module.stack_test_static_variable.aws_s3_bucket.storage will be created
        + resource "aws_s3_bucket" "storage" {
            + acceleration_status         = (known after apply)
            + acl                         = (known after apply)
            + arn                         = (known after apply)
            + bucket                      = (known after apply)
            + bucket_domain_name          = (known after apply)
            + bucket_prefix               = (known after apply)
            + bucket_region               = (known after apply)
            + bucket_regional_domain_name = (known after apply)
            + force_destroy               = false
            + hosted_zone_id              = (known after apply)
            + id                          = (known after apply)
            + object_lock_enabled         = (known after apply)
            + policy                      = (known after apply)
            + region                      = "eu-west-1"
            + request_payer               = (known after apply)
            + tags_all                    = {
                + "cost_center" = "1979"
                + "environment" = "joe's garage"
                + "owner"       = "frank zappa"
                }
            + website_domain              = (known after apply)
            + website_endpoint            = (known after apply)

            + cors_rule (known after apply)

            + grant (known after apply)

            + lifecycle_rule (known after apply)

            + logging (known after apply)

            + object_lock_configuration (known after apply)

            + replication_configuration (known after apply)

            + server_side_encryption_configuration (known after apply)

            + versioning (known after apply)

            + website (known after apply)
            }

        # module.stack_test_static_variable.aws_s3_bucket_policy.storage will be created
        + resource "aws_s3_bucket_policy" "storage" {
            + bucket = (known after apply)
            + id     = (known after apply)
            + policy = (known after apply)
            + region = "eu-west-1"
            }

        Plan: 2 to add, 0 to change, 0 to destroy.
        ╷
        │ Warning: Backend configuration ignored
        │
        │   on ../config.tf line 2, in terraform:
        │    2:   backend "s3" {}
        │
        │ Any selected backend applies to the entire configuration, so OpenTofu expects provider configurations only in the root module.
        │
        │ This is a warning rather than an error because it's sometimes convenient to temporarily call a root module as a child module for testing
        │ purposes, but this backend configuration block will have no effect.
        ╵

        ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

        Saved the plan to: __snapshots__/_1759855219.plan

        To perform exactly these actions, run the following command to apply:
            tofu apply "__snapshots__/_1759855219.plan"
        ..

        ------------------------------------------------------------ snapshot report summary -------------------------------------------------------------
        2 snapshots passed. 2 unused snapshots deleted.

        Deleted unknown snapshot collection (tests/__snapshots__/_1759855219.plan)
        Deleted unknown snapshot collection (tests/__snapshots__/_1759855219.json)
        =============================================================== 2 passed in 6.19s ================================================================

#. This will generate the snapshots with the module `synthesis <https://github.com/joaorodrig/terraform-snapshot-test/blob/main/examples/aws-s3-bucket/tests/__snapshots__/test_terraform_snapshot/test_synthesizes_properly.json>`_ and `planned values <https://github.com/joaorodrig/terraform-snapshot-test/blob/main/examples/aws-s3-bucket/tests/__snapshots__/test_terraform_snapshot/test_planned_values.json>`_ for the different tests, which will be committed to the repository;

#. To run these unit tests as part of the CI/CD pipeline, you could then run the following command from the Terraform / OpenTofu root, and verify that code being built meets the expected state as defined and verified by the engineer as per the snapshot:

    ::

        pytest

#. Example of the output of the test comparison with the snapshots:

    ::

        ============================================================== test session starts ===============================================================
        platform linux -- Python 3.12.3, pytest-8.4.2, pluggy-1.6.0
        rootdir: /home/user/workspace/github/terraform-snapshot-test/tests/aws-s3-bucket
        configfile: pytest.ini
        plugins: syrupy-5.0.0, order-1.3.0, env-1.1.5
        collected 2 items

        tests/test_terraform_snapshot.py ..                                                                                                        [100%]

        ------------------------------------------------------------ snapshot report summary -------------------------------------------------------------
        2 snapshots passed. 4 snapshots unused.

        Re-run pytest with --snapshot-update to delete unused snapshots.
        =============================================================== 2 passed in 6.11s ================================================================


Expectations Example
====================

If you want to extend the use of expectations, you can create an `assertions <https://github.com/joaorodrig/terraform-snapshot-test/tree/main/examples/aws-s3-bucket/tests/expectations>`_ folder in the `tests <https://github.com/joaorodrig/terraform-snapshot-test/tree/main/examples/aws-s3-bucket/tests>`_ folder of the terraform stack.

In this folder, you can create one YAML file per stack which you want to test. Here's the syntax of the expectations YAML file:

::

    module: module.stack_test_static_variable
    description: Test stack static variable assertions

    synthesis:
        assertions: {}

    planned_values:
        assertions: {}


In the expecations section you can write the objects and configuration which you want to ensure will exist in the ``synthesis`` and ``planned_values`` snapshots.

You can also specificy the following macros / key words as part of the assertion criteria:

- ``$MODULE``: Replaced at runtime by the module name (taken from the top of the assertions file);
- ``$NOTNULL``: When matching a scalar property, ensures the value of the property is non-null;


See here two examples of expecations:

- `AWS S3 Bucket synthesis snapshot <https://github.com/joaorodrig/terraform-snapshot-test/blob/main/examples/aws-s3-bucket/tests/__snapshots__/test_terraform_snapshot/test_synthesizes_properly.json>`_, `AWS S3 Bucket planned_values snapshot <https://github.com/joaorodrig/terraform-snapshot-test/blob/main/examples/aws-s3-bucket/tests/__snapshots__/test_terraform_snapshot/test_planned_values.json>`_, `AWS S3 Bucket expectations <https://github.com/joaorodrig/terraform-snapshot-test/tree/main/examples/aws-s3-bucket/tests/expectations>`_;
- AWS Transit Gateway and AWS Network Firewall, ensuring that the firewall exists in the prod test stack (e.g. test conditionals): `synthesis snapshot <https://github.com/joaorodrig/terraform-snapshot-test/blob/main/examples/aws-tgw-anf/tests/__snapshots__/test_terraform_snapshot/test_synthesizes_properly.json>`_, `planned_values snapshot <https://github.com/joaorodrig/terraform-snapshot-test/blob/main/examples/aws-tgw-anf/tests/__snapshots__/test_terraform_snapshot/test_planned_values.json>`_, `expecations <https://github.com/joaorodrig/terraform-snapshot-test/tree/main/examples/aws-tgw-anf/tests/expectations>`_:


Running the Examples
--------------------

To run the examples you need to have read-only access to the relevant APIs:

- Simple example of `AWS S3 Bucket <https://github.com/joaorodrig/terraform-snapshot-test/tree/main/examples/aws-s3-bucket/>`_, with static dependency variables (and commented examples of referended and remote state dependencies);
- Simple example of `GitLab Project <https://github.com/joaorodrig/terraform-snapshot-test/tree/main/examples/gitlab-project>`_, with with static dependency variables (and commented examples of referended and remote state dependencies);
- Simple example of `GitHub Repository <https://github.com/joaorodrig/terraform-snapshot-test/tree/main/examples/github-repository>`_, with static dependency variables;
- Expectations example of `AWS Transit Gateway and AWS Network Firewall <https://github.com/joaorodrig/terraform-snapshot-test/tree/main/examples/aws-tgw-anf>`_, with static dependency variables and expectations for non-prod (without firewall) and prod (with firewall);


Future Work
===========

- Add more examples of different providers;
- Any other relevant requests by the community;
