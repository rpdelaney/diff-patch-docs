# How to request changes to text files during maintenance

<!-- mdformat-toc start --slug=github --no-anchors --maxlevel=3 --minlevel=1 -->

- [How to request changes to text files during maintenance](#how-to-request-changes-to-text-files-during-maintenance)
  - [Executive summary](#executive-summary)
  - [The Problem](#the-problem)
  - [Enter diff-patch](#enter-diff-patch)
    - [Prerequisites](#prerequisites)
    - [As the requester](#as-the-requester)
    - [As the maintainer](#as-the-maintainer)
    - [Troubleshooting](#troubleshooting)

<!-- mdformat-toc end -->

## Executive summary

1. Sometimes we need to request that someone else edit code, configuration
   files, or other text files on production hosts.
1. Ensuring that only exactly the requested changes are made is hard for
   humans: both the requester and the engineer performing the change.
1. However, it's easy for computers.
1. Therefore, use `diff` and `patch` on the command line:

```console
$ # Create a patch to attach to a change request
$ cp file.conf file.conf.new
$ vim file.conf.new
$ diff -u file.conf file.conf.new > file_diff.patch
```

```console
$ # Apply a patch from a change request
$ patch -u < file_diff.patch
```

## The Problem

Let's walk through a hypothetical scenario showing why determinism in change
requests is important.

Suppose you are assigned a ticket that says this:

> Background:
>
> Two problems have been identified with [cli.py](/cli.py) that need
> remediation:
>
> - The variable named "url" is vague and should be more descriptive.
> - There is a bug with the API this code is consuming where if a trailing "/"
>   is not included in the endpoint URL, the API will return a 404.
>
> AC:
>
> - Rename the "url" variable to "endpoint_url" where appropriate.
> - Add a trailing `/` to the endpoint URL where appropriate.

The engineer who wrote this ticket already took the time to understand this
code and the problems with it, but remediation work in production has to be
done during a maintenance window. Therefore, they've written this ticket.

Now you have to make the change, but you are coming into all this fresh. You 
don't have context, you don't understand the code you're looking at, and worse, 
you're in an after-hours maintenance window with the clock ticking -- everyone 
is waiting for you to figure this out so that they can go home! Now you have to 
do all that discovery work _again_ and under pressure.

Not good!

It would be better if the requester had actually given you the code they want
you to put on the production server. For instance, we've had some change
requests like this:

<details><summary>Change request</summary>

```python
     API_FRAGMENT = "rest/api/2/search"
     endpoint_url = urljoin(JIRA_BASE_URL, API_FRAGMENT) + "/"

     response = requests.get(
         url=endpoint_url,
```

```python
     API_FRAGMENT = "api/2.0/fo/scan"
     endpoint_url = urljoin(QUALYS_BASE_URL, API_FRAGMENT) + "/"

     response = requests.post(
         url=endpoint_url,
```

```python
     API_FRAGMENT = "api/2.0/fo/scan"
     endpoint_url = urljoin(QUALYS_BASE_URL, API_FRAGMENT) + "/"

     response = requests.post(
```

```python
     API_FRAGMENT = "api/2.0/fo/knowledge_base/vuln/"
     endpoint_url = urljoin(QUALYS_BASE_URL, API_FRAGMENT) + "/"

     response = requests.post(
```

</details>

That's more explicit! But... where exactly should all these snippets of code go
in [cli.py](/cli.py)? Are they meant to be _added_ somewhere, or should you
_replace_ something in cli.py with what's in the change request? So you find
yourself scrolling around in code at 8:00 PM on a Thursday trying to make sense
of it anyway.

Learning from all this, you might amend the process for next time to ask for
even clearer instructions. Along with each snippet, we need requesters to be
explicit about more stuff:

1. Should this snippet be added, or should it replace something?
1. If it should replace something, what should it replace?
1. On which exact lines are the additions or substitutions to take place?

Doing all that would help you during the maintenance, but it helps by shifting
the burden of tedium from you to the requester. And we're still manually
cross-checking line numbers and eyeballing code we don't really understand to
make sure we don't miss anything.

**Don't we have computers for this sort of work?!**

## Enter diff-patch

`diff` is a command line utility that compares two files line by line and
prints differences between them in a machine-readable format. Its output is
colloquially known as a "diff" or "patch".

`patch` is a sister utility that reads a patch and applies it to an existing
file.

A patch file can be used to suggest changes to code, configuration files, or
other plain-text in a deterministic way. By distributing a patch, we can ensure
that _exactly_ the requested changes will be made by the person who applies it.

This document gives a brief overview of how to set up and use both these tools
to create and apply patch files.

### Prerequisites

If you are working locally, beware that macOS may ship with BSD diffutils
installed by default. You need GNU diffutils:

```console
$ # Install GNU diffutils
$ brew install diffutils
[...]
$
```

On most remote linux hosts, diffutils will be pre-installed by default.

Ensure that you have GNU versions on the PATH:

```console
$ diff --version
diff (GNU diffutils) X.X   <-- GNU! Correct!
Copyright (C) 2021 Free Software Foundation, Inc.
License GPLv3+: GNU GPL version 3 or later <https://gnu.org/licenses/gpl.html>.
[...]
$ patch --version
patch X.X.X
Copyright (C) 1988 Larry Wall
Copyright (C) 2002 Free Software Foundation, Inc.  <--  Free Software Foundation! Correct!
[...]
$
```

### As the requester

#### Create a patch file

If you are requesting changes, you should create a patch file to attach to the
ticket with your change request. For example, here's how I did it with
[cli.py](/cli.py) for this demonstration:

```console
$ # Make a backup of the file you want to change.
$ cp cli.py cli_after.py
$ # Edit the backup file and make the needed changes to it.
$ vim cli_after.py
$ # Create a unified patch file from the differences between the original and the backup.
$ diff --unified cli.py cli_after.py > cli_diff.patch
```

Check out the results!

<details><summary>cli_diff.patch</summary>

```diff
--- cli.py	2022-06-30 10:47:59.303902934 -0400
+++ cli_after.py	2022-06-30 09:55:27.003231542 -0400
@@ -28,10 +28,10 @@
 def jira() -> None:
     """Send a request to the Jira search API and print the response."""
     API_FRAGMENT = "rest/api/2/search"
-    url = urljoin(JIRA_BASE_URL, API_FRAGMENT)
+    endpoint_url = urljoin(JIRA_BASE_URL, API_FRAGMENT) + "/"

     response = requests.get(
-        url,
+        url=endpoint_url,
         auth=requests.auth.HTTPBasicAuth(
             os.environ["JIRA_USERNAME"], os.environ["JIRA_PASSWORD"]
         ),
@@ -55,10 +55,10 @@
     of all finished scans, and convert the response from XML to JSON
     before printing."""
     API_FRAGMENT = "api/2.0/fo/scan"
-    url = urljoin(QUALYS_BASE_URL, API_FRAGMENT)
+    endpoint_url = urljoin(QUALYS_BASE_URL, API_FRAGMENT) + "/"

     response = requests.post(
-        url=url,
+        url=endpoint_url,
         auth=(os.environ["QUALYS_USERNAME"], os.environ["QUALYS_PASSWORD"]),
         headers={"X-Requested-With": "application/python"},
         data={"action": "list", "state": "Finished"},
@@ -79,10 +79,10 @@
     scans. Therefore, the scan_id argument is required.
     """
     API_FRAGMENT = "api/2.0/fo/scan"
-    url = urljoin(QUALYS_BASE_URL, API_FRAGMENT)
+    endpoint_url = urljoin(QUALYS_BASE_URL, API_FRAGMENT) + "/"

     response = requests.post(
-        url=url,
+        url=endpoint_url,
         auth=requests.auth.HTTPBasicAuth(
             os.environ["QUALYS_USERNAME"], os.environ["QUALYS_PASSWORD"]
         ),
@@ -114,10 +114,10 @@
     a specific vulnerability, and convert the response from XML to JSON before
     printing."""
     API_FRAGMENT = "api/2.0/fo/knowledge_base/vuln/"
-    url = urljoin(QUALYS_BASE_URL, API_FRAGMENT)
+    endpoint_url = urljoin(QUALYS_BASE_URL, API_FRAGMENT) + "/"

     response = requests.post(
-        url=url,
+        url=endpoint_url,
         auth=requests.auth.HTTPBasicAuth(
             os.environ["QUALYS_USERNAME"], os.environ["QUALYS_PASSWORD"]
         ),
```

</details>

What we have here is a machine-readable instruction set for making the changes.

#### Optional: Test your patch file

If it's safe to do so, you can test it out by applying the patch to the edited
file in reverse. Try cloning this repo and trying it out yourself:

```console
$ # Apply the patch
$ patch --unified < cli_diff.patch
$ # See what it did
$ git diff
[...]
$ # Apply the patch in reverse (this is like an "undo"):
$ patch --unified --reverse < cli_diff.patch
$ # Everything's back to normal!
$ git diff
$
```

#### Making the request

Now that you have your patch, you can attach `cli_diff.patch` to the ticket
requesting the change. Do not copy the patch into the ticket description.

### As the maintainer

Now we have a ticket with everything we need:

1. A patch file.
1. The hostname or address where the patch is to be applied.
1. The path to the file the patch is to be applied to.

Download the patch file from the ticket attachments.

```console
$ # Copy the patch file to the remote host
$ scp cli_diff.patch <USER>@<HOSTNAME>:/tmp/
[...]
$ # Log in
$ ssh <USER>@<HOSTNAME>
[...]
$ # cd to the file to be patched and apply
$ cd /path/to/file && patch -u </tmp/cli_diff.patch
patching file cli.py
$ # Optional: Remove the patch file.
$ rm /tmp/cli_diff.patch
$ # Done! Log out
$ exit
```

Done! The change is completed.

### Troubleshooting

#### Can't find file to patch

You are in the wrong directory. Change directory to the path expected by the
patch file.

A unified patch specifies the file names _with a relative path_ to the files
that are to be changed when the patch is applied. For example, in the exercise
above, our patch file starts like this:

```diff
--- cli.py	2022-06-30 10:47:59.303902934 -0400
+++ cli_after.py	2022-06-30 09:55:27.003231542 -0400
[...]
```

That means that when applying, `patch` will look for a file `./cli.py` in the
current working directory. If it does not find a file by that name, you might
get an error like this:

```
can't find file to patch at input line 3
Perhaps you should have used the -p or --strip option?
The text leading up to this was:
--------------------------
|--- cli.py     2022-06-30 10:47:59.303902934 -0400
|+++ cli_after.py       2022-06-30 09:55:27.003231542 -0400
--------------------------
File to patch:
```
