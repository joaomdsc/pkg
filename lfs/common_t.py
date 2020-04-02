# common_t.py

import unittest
from subprocess import run, PIPE, STDOUT
from common import replace_values, commentify
import common

#-------------------------------------------------------------------------------
# I want stdout to be unbuffered, always
#-------------------------------------------------------------------------------

class Unbuffered(object):
    def __init__(self, stream):
        self.stream = stream
    def write(self, data):
        self.stream.write(data)
        self.stream.flush()
    def __getattr__(self, attr):
        return getattr(self.stream, attr)

import sys
sys.stdout = Unbuffered(sys.stdout)

# -----------------------------------------------------------------------------
# ReplaceTests
# -----------------------------------------------------------------------------

class ReplaceTest(unittest.TestCase):
    """Test the replace_values function."""

    # -------------------------------------------------------------------------
    # test01
    # -------------------------------------------------------------------------

    def test_replace_01(self):
        """Simple replacements"""
        s = 'hello'
        vals = []
        t = 'hello'
        self.assertEqual(t, replace_values(s, vals))

        s = '<code></code>'
        vals = ['x']
        t = 'x'
        self.assertEqual(t, replace_values(s, vals))

        s = '<code>x</code>'
        vals = ['y']
        t = 'y'
        self.assertEqual(t, replace_values(s, vals))

        s = 'abc<code>x</code>abc'
        vals = ['y']
        t = 'abcyabc'
        self.assertEqual(t, replace_values(s, vals))

        s = '  \t<code> x</code>   \t'
        vals = ['y']
        t = '  \ty   \t'
        self.assertEqual(t, replace_values(s, vals))

        # \u can be interpreted as a unicode escape sequence, use a raw string
        # to avoid that
        s = r'abc \u xyz <code>hello</code> abc'
        vals = ['goodbye']
        t = r'abc \u xyz goodbye abc'
        self.assertEqual(t, replace_values(s, vals))

    def test_replace_02(self):
        """Double replacements"""
        s = '<code></code><code></code>'
        vals = ['a', 'b']
        t = 'ab'
        self.assertEqual(t, replace_values(s, vals))

        s = '<code>x</code><code>y</code>'
        vals = ['a', 'b']
        t = 'ab'
        self.assertEqual(t, replace_values(s, vals))

        s = 'abc<code>x</code>abc<code>x</code>abc'
        vals = ['1', '2']
        t = 'abc1abc2abc'
        self.assertEqual(t, replace_values(s, vals))

        s = '  \t<code> x</code>   \t<code> x</code>\t   '
        vals = ['8', '9']
        t = '  \t8   \t9\t   '
        self.assertEqual(t, replace_values(s, vals))

    def test_replace_03(self):
        """Multiline replacements"""
        s = """<code>x</code>
<code>y</code>
<code>y</code>"""
        vals = ['x', 'y', 'z']
        t = """x
y
z"""
        self.assertEqual(t, replace_values(s, vals))

        s = """
zertzertabc<code>x</code>oiuoyi
rgsfg<code>y</code>dfgsdfgs
cbxcvbx<code>y</code>sdfgsd
sgsdfgsdf"""
        vals = ['x', 'y', 'z']
        t = """
zertzertabcxoiuoyi
rgsfgydfgsdfgs
cbxcvbxzsdfgsd
sgsdfgsdf"""
        self.assertEqual(t, replace_values(s, vals))

    def test_replace_04(self):
        """Continuation lines"""

        s = """abc \
def"""
        vals = []
        t = """abc \
def"""
        self.assertEqual(t, replace_values(s, vals))
        
        s = """abc <code>hello</code> \
def"""
        vals = ['bye']
        t = """abc bye \
def"""
        self.assertEqual(t, replace_values(s, vals))

        s = """abc \
def <code>bonjour</code>"""
        vals = ['bonsoir']
        t = """abc \
def bonsoir"""
        self.assertEqual(t, replace_values(s, vals))
        
        # Deux continuations, trois lignes
        s = """abc \
def \
ghi"""
        vals = []
        t = """abc \
def \
ghi"""
        self.assertEqual(t, replace_values(s, vals))

        # \u can be interpreted as a unicode escape sequence, use a raw string
        # to avoid that
        s = r'abc \u xyz \
<code>hello</code> abc'
        vals = ['goodbye']
        t = r'abc \u xyz \
goodbye abc'
        self.assertEqual(t, replace_values(s, vals))

    def test_replace_05(self):
        """LFS directives examples"""
        s = """echo "export LFS='<code>/mnt/lfs</code>'" >> $HOME/.bashrc
export LFS=<code>/mnt/lfs</code>
echo \$LFS=$LFS"""
        vals = ['/mnt/lfs', '/mnt/lfs']
        t = """echo "export LFS='/mnt/lfs'" >> $HOME/.bashrc
export LFS=/mnt/lfs
echo \$LFS=$LFS"""
        self.assertEqual(t, replace_values(s, vals))

        s = """cp <code>pkg_repository</code>/*.* $LFS/sources"""
        vals = ['/home/joao/lfs/9.0-systemd/pkgs']
        t = """cp /home/joao/lfs/9.0-systemd/pkgs/*.* $LFS/sources"""
        self.assertEqual(t, replace_values(s, vals))

        # Example from 6.04, with no replacement
        s = r"""chroot "$LFS" /tools/bin/env -i \
HOME=/root \
TERM="$TERM" \
PS1='(lfs chroot) \u:\w\$ ' \
PATH=/bin:/usr/bin:/sbin:/usr/sbin:/tools/bin \
/tools/bin/bash --login +h /var/tmp/lfs/script_03.sh"""
        vals = []
        t = r"""chroot "$LFS" /tools/bin/env -i \
HOME=/root \
TERM="$TERM" \
PS1='(lfs chroot) \u:\w\$ ' \
PATH=/bin:/usr/bin:/sbin:/usr/sbin:/tools/bin \
/tools/bin/bash --login +h /var/tmp/lfs/script_03.sh"""
        self.assertEqual(t, replace_values(s, vals))

        # Example from 6.04, with an added replacement
        s = r"""chroot "$LFS" <code>env</code> -i \
HOME=/root \
TERM="$TERM" \
PS1='(lfs chroot) \u:\w\$ ' \
PATH=/bin:/usr/bin:/sbin:/usr/sbin:/tools/bin \
/tools/bin/bash --login +h /var/tmp/lfs/script_03.sh"""
        vals = ['/tools/bin/env']
        t = r"""chroot "$LFS" /tools/bin/env -i \
HOME=/root \
TERM="$TERM" \
PS1='(lfs chroot) \u:\w\$ ' \
PATH=/bin:/usr/bin:/sbin:/usr/sbin:/tools/bin \
/tools/bin/bash --login +h /var/tmp/lfs/script_03.sh"""
        self.assertEqual(t, replace_values(s, vals))

        # Example from 6.04, adding the LFS variable
        s = r"""chroot "$LFS" /tools/bin/env -i \
LFS=<code></code> \
HOME=/root \
TERM="$TERM" \
PS1='(lfs chroot) \u:\w\$ ' \
PATH=/bin:/usr/bin:/sbin:/usr/sbin:/tools/bin \
/tools/bin/bash --login +h /var/tmp/lfs/script_03.sh"""
        vals = ['/mnt/lfs']
        t = r"""chroot "$LFS" /tools/bin/env -i \
LFS=/mnt/lfs \
HOME=/root \
TERM="$TERM" \
PS1='(lfs chroot) \u:\w\$ ' \
PATH=/bin:/usr/bin:/sbin:/usr/sbin:/tools/bin \
/tools/bin/bash --login +h /var/tmp/lfs/script_03.sh"""
        self.assertEqual(t, replace_values(s, vals))

# -----------------------------------------------------------------------------
# CommentifyTests
# -----------------------------------------------------------------------------

class CommentifyTests(unittest.TestCase):
    """Test the commentify function."""

    def uncommentify(s):
        """Run s code, remove the leading comment character and space.

        This will return the initial text.
        """
        r = run(['bash', '-c', s], stdout=PIPE, stderr=STDOUT)
        t = r.stdout.decode()
        # Remove '# ' from the beginning of lines
        t = '\n'.join([k[2:] for k in t.split('\n')])
        return t
    
        
    # -------------------------------------------------------------------------
    # test01
    # -------------------------------------------------------------------------

    def test_commentify_01(self):
        """Single line"""
        s = """sed -i '/asm.socket.h/a# include <linux/sockios.h>'
"""
        self.assertEqual(s, CommentifyTests.uncommentify(commentify(s)))
        
    # -------------------------------------------------------------------------
    # test02
    # -------------------------------------------------------------------------

    def test_commentify_02(self):
        """Multiple lines"""
        s = r"""chroot "$LFS" /usr/bin/env -i \
HOME=/root \
TERM="$TERM" \
PS1='(lfs chroot) \u:\w\$ ' \
PATH=/bin:/usr/bin:/sbin:/usr/sbin \
/bin/bash --login /script_05.sh

"""
        self.assertEqual(s, CommentifyTests.uncommentify(commentify(s)))

# -----------------------------------------------------------------------------
# ErrorTests
# -----------------------------------------------------------------------------

class ErrorTests(unittest.TestCase):
    """Test error cases."""
        
    # -------------------------------------------------------------------------
    # test01
    # -------------------------------------------------------------------------

    def test_errors_01(self):
        """No placeholder"""
        s = 'hello'
        vals = ['bye']
        with self.assertRaises(RuntimeError):
            replace_values(s, vals)
        
    # -------------------------------------------------------------------------
    # test01
    # -------------------------------------------------------------------------

    # Having more values than placeholders is not an error (could be a warning)
    
    def test_errors_00(self):
        """No  placeholder"""
        s = 'hello'
        vals = ['bye']
        t = 'hello'
        self.assertEqual(t, replace_values(s, vals))

    def test_errors_01(self):
        """Not enough placeholders 1"""
        s = 'hello <code>someone</code>'
        vals = ['john', 'paul']
        t = 'hello john'
        self.assertEqual(t, replace_values(s, vals))

    def test_errors_02(self):
        """Not enough placeholders 2"""
        s = """hello <code>someone</code> \
bye <code>someone else</code>
"""
        vals = ['john', 'paul', 'mary']
        t = """hello john \
bye paul
"""
        self.assertEqual(t, replace_values(s, vals))

    def test_errors_03(self):
        """No values, no placeholders"""
        s = 'hello'
        vals = []
        t = 'hello'
        self.assertEqual(t, replace_values(s, vals))

    def test_errors_04(self):
        """Not enough values 1"""
        s = 'hello <code>someone</code>'
        vals = []
        with self.assertRaises(RuntimeError):
            replace_values(s, vals)

    def test_errors_05(self):
        """Not enough values 2"""
        s = 'hello <code>someone</code><code>bye</code>foo'
        vals = ['first']
        with self.assertRaises(RuntimeError):
            replace_values(s, vals)

if __name__ == '__main__':
    unittest.main(verbosity=2)

