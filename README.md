etcrebase
=========

`etcrebase` is a tool that allows to rebase configuration changes from an /etc directory
to another.

It's only useful for specific usecases, you probably don't need it.

Currently it implies running in an openSUSE MicroOS system, but it can be adapted
to work on other distributions as well.

How does it work?
----------------

`etcrebase` is rather simple, it reads a specified list of configurations to handle
([this is the one included by default](./data/configs-microos.txt)) and translates
it to a list of actions to do on the new tree.

For example:

    /etc/fstab
    /etc/crypttab
    /etc/passwd
    /etc/shadow
    /etc/group
    /etc/subgid
    /etc/subuid

a different handler can be specified using a semicolon, like this:

    /etc/subuid;copyprefertarget

in this case the `copyprefertarget` handler is used instead.

The default handler is `copy`, which simply copies the file in-place.

Handlers can hint a file to use directly in the code, for example:

```python
@register_action("myaction", "etc/fstab")
class MyAction(etcrebase.Action):
    pass
```

will register that handler as `myaction`, and hints that `/etc/fstab` should use
that handler by default.

The configuration list file can override this choice at any time:

    /etc/fstab
    /etc/fstab;myaction

are equivalent, while

    /etc/fstab
    /etc/fstab;copy

will reset it to use the copy action. Actions are evaluated top-bottom.

Directories are supported as well:

    /etc/sysconfig/
    /etc/sysconfig/windowmanager;copyprefertarget

This will use the default handler for every file in /etc/sysconfig, and uses
`copyprefertarget` on /etc/sysconfig/windowmanager.

Available handlers
------------------

Right now, these are the current available handlers:

* copy
* copyprefertarget
* mergepasswd (default for /etc/passwd)
* mergeshadow (default for /etc/shadow)
* mergegroup (default for /etc/group)
* microosfstab (default for /etc/fstab)
