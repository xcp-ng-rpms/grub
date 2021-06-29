# Modules always contain just 32-bit code
%define _libdir %{_exec_prefix}/lib

# 64bit intel machines use 32bit boot loader
# (We cannot just redefine _target_cpu, as we'd get i386.rpm packages then)
%ifarch x86_64
%define _target_platform i386-%{_vendor}-%{_target_os}%{?_gnu}
%endif
# sparc is always compiled 64 bit
%ifarch %{sparc}
%define _target_platform sparc64-%{_vendor}-%{_target_os}%{?_gnu}
%endif

%if ! 0%{?efi:1}

%global efiarchs x86_64

%ifarch %{ix86}
%global grubefiarch i386-efi
%global grubefiname grubia32.efi
%global grubeficdname gcdia32.efi
%endif
%ifarch x86_64
%global grubefiarch %{_arch}-efi
%global grubefiname grubx64.efi
%global grubeficdname gcdx64.efi
%endif

%global grubefibootname bootx64.efi

%global efidir xenserver
%global efibootdir boot

%endif

%undefine _missing_build_ids_terminate_build

Name:           grub
Epoch:          1
Version:        2.02
Release:        3.0.0%{?dist}
Summary:        Bootloader with support for Linux, Multiboot and more

Group:          System Environment/Base
License:        GPLv3+
URL:            http://www.gnu.org/software/grub/
Obsoletes:      grub < 1:0.98

Source0: https://code.citrite.net/rest/archive/latest/projects/XSU/repos/grub/archive?at=2.02&format=tar.gz&prefix=grub-2.02#/grub-2.02.tar.gz

Patch0: wait-before-drain.patch

Provides: gitsha(https://code.citrite.net/rest/archive/latest/projects/XSU/repos/grub/archive?at=2.02&format=tar.gz&prefix=grub-2.02#/grub-2.02.tar.gz) = e54c99aaff5e5f6f5d3b06028506c57e66d8ef77
Provides: gitsha(https://code.citrite.net/rest/archive/latest/projects/XS/repos/grub.pg/archive?format=tar&at=v3.0.0#/grub.patches.tar) = 47d84fa0111e1e40e2a0725c98f066b95f2ee71c


BuildRequires:  gcc
BuildRequires:  flex bison binutils python
BuildRequires:  ncurses-devel xz-devel
BuildRequires:  freetype-devel libusb-devel
%ifarch %{sparc} x86_64
# sparc builds need 64 bit glibc-devel - also for 32 bit userland
BuildRequires:  %{_exec_prefix}/lib64/crt1.o glibc-static
%else
# ppc64 builds need the ppc crt1.o
BuildRequires:  %{_exec_prefix}/lib/crt1.o glibc-static
%endif
BuildRequires:  autoconf automake autogen device-mapper-devel
BuildRequires:  freetype-devel gettext-devel git
BuildRequires:  texinfo
BuildRequires:  help2man

Requires:       gettext os-prober which file
Requires:       %{name}-tools = %{epoch}:%{version}-%{release}
Requires(pre):  dracut
Requires(post): dracut

ExcludeArch:    s390 s390x %{arm}
Obsoletes:      grub2 <= 2.00-20%{?dist}

%description
The GRand Unified Bootloader (GRUB) is a highly configurable and customizable
bootloader with modular architecture.  It support rich varietyof kernel formats,
file systems, computer architectures and hardware devices.  This subpackage
provides support for PC BIOS systems.

%ifarch %{efiarchs}
%package efi
Provides: gitsha(https://code.citrite.net/rest/archive/latest/projects/XSU/repos/grub/archive?at=2.02&format=tar.gz&prefix=grub-2.02#/grub-2.02.tar.gz) = e54c99aaff5e5f6f5d3b06028506c57e66d8ef77
Provides: gitsha(https://code.citrite.net/rest/archive/latest/projects/XS/repos/grub.pg/archive?format=tar&at=v3.0.0#/grub.patches.tar) = 47d84fa0111e1e40e2a0725c98f066b95f2ee71c
Summary:        GRUB for EFI systems.
Group:          System Environment/Base
Requires:       %{name}-tools = %{epoch}:%{version}-%{release}
Obsoletes:      grub2-efi <= 2.00-20%{?dist}

%description efi
The GRand Unified Bootloader (GRUB) is a highly configurable and customizable
bootloader with modular architecture.  It support rich varietyof kernel formats,
file systems, computer architectures and hardware devices.  This subpackage
provides support for EFI systems.
%endif

%package tools
Provides: gitsha(https://code.citrite.net/rest/archive/latest/projects/XSU/repos/grub/archive?at=2.02&format=tar.gz&prefix=grub-2.02#/grub-2.02.tar.gz) = e54c99aaff5e5f6f5d3b06028506c57e66d8ef77
Provides: gitsha(https://code.citrite.net/rest/archive/latest/projects/XS/repos/grub.pg/archive?format=tar&at=v3.0.0#/grub.patches.tar) = 47d84fa0111e1e40e2a0725c98f066b95f2ee71c
Summary:        Support tools for GRUB.
Group:          System Environment/Base
Requires:       gettext os-prober which file system-logos

%description tools
The GRand Unified Bootloader (GRUB) is a highly configurable and customizable
bootloader with modular architecture.  It support rich varietyof kernel formats,
file systems, computer architectures and hardware devices.  This subpackage
provides tools for support of all platforms.

%prep
%autosetup -p1
mkdir ../%{name}-efi-%{version}
cp -a . ../%{name}-efi-%{version}

%build
%ifarch %{efiarchs}
pushd ../%{name}-efi-%{version}
./autogen.sh
%configure \
    CFLAGS="$(echo $RPM_OPT_FLAGS | sed \
        -e 's/-O.//g' \
        -e 's/-fstack-protector[[:alpha:]-]\+//g' \
        -e 's/-fstack-protector//g' \
        -e 's/--param=ssp-buffer-size=4//g' \
        -e 's/-mregparm=3/-mregparm=4/g' \
        -e 's/-fexceptions//g' \
        -e 's/-fasynchronous-unwind-tables//g' \
        -e 's/-m64//g' \
        -e 's/^/ -fno-strict-aliasing /' \
        -e 's/^/ -fno-stack-protector /' \
                )"                                              \
    TARGET_LDFLAGS=-static \
        --with-platform=efi \
    --with-grubdir=%{name} \
        --program-transform-name=s,grub,%{name}, \
    --disable-grub-mount \
    --disable-werror
make %{?_smp_mflags}

GRUB_MODULES="all_video boot btrfs cat chain configfile echo efifwsetup \
        efinet ext2 fat font gfxmenu gfxterm gzio halt hfsplus http iso9660 \
        jpeg linux loadenv lsefimmap lsmmap lvm minicmd normal part_apple part_msdos \
        part_gpt password_pbkdf2 png reboot search search_fs_uuid \
        search_fs_file search_label serial sleep test video xfs \
        mdraid09 mdraid1x multiboot2 multiboot tftp"
./grub-mkimage -O %{grubefiarch} -o %{grubeficdname} -p /EFI/BOOT \
        -d grub-core ${GRUB_MODULES}
./grub-mkimage -O %{grubefiarch} -o %{grubefiname} -p /EFI/%{efidir} \
        -d grub-core ${GRUB_MODULES}
popd
%endif

./autogen.sh
# -static is needed so that autoconf script is able to link
# test that looks for _start symbol on 64 bit platforms
%ifarch %{sparc} ppc ppc64
%define platform ieee1275
%else
%define platform pc
%endif
%configure \
    CFLAGS="$(echo $RPM_OPT_FLAGS | sed \
        -e 's/-O.//g' \
        -e 's/-fstack-protector[[:alpha:]-]\+//g' \
        -e 's/-fstack-protector//g' \
        -e 's/--param=ssp-buffer-size=4//g' \
        -e 's/-mregparm=3/-mregparm=4/g' \
        -e 's/-fexceptions//g' \
        -e 's/-m64//g' \
        -e 's/-fasynchronous-unwind-tables//g' \
        -e 's/-mcpu=power7/-mcpu=power6/g' \
        -e 's/^/ -fno-strict-aliasing /' )" \
    TARGET_LDFLAGS=-static \
        --with-platform=%{platform} \
    --with-grubdir=%{name} \
        --program-transform-name=s,grub,%{name}, \
    --enable-man-pages \
    --disable-grub-mount \
    --disable-werror
make %{?_smp_mflags}

sed -i -e 's,(grub),(%{name}),g' \
    -e 's,grub.info,%{name}.info,g' \
    -e 's,\* GRUB:,* GRUB2:,g' \
    -e 's,/boot/grub/,/boot/%{name}/,g' \
    -e 's,\([^-]\)grub-\([a-z]\),\1%{name}-\2,g' \
    docs/grub.info
sed -i -e 's,grub-dev,%{name}-dev,g' docs/grub-dev.info

/usr/bin/makeinfo --html --no-split -I docs -o grub-dev.html docs/grub-dev.texi
/usr/bin/makeinfo --html --no-split -I docs -o grub.html docs/grub.texi
sed -i    -e 's,/boot/grub/,/boot/%{name}/,g' \
    -e 's,\([^-]\)grub-\([a-z]\),\1%{name}-\2,g' \
    grub.html

%install
set -e
rm -fr $RPM_BUILD_ROOT

%ifarch %{efiarchs}
pushd ../%{name}-efi-%{version}
make DESTDIR=$RPM_BUILD_ROOT install
find $RPM_BUILD_ROOT -iname "*.module" -exec chmod a-x {} \;

# Ghost config file
install -m 755 -d $RPM_BUILD_ROOT/boot/efi/EFI/%{efidir}/
touch $RPM_BUILD_ROOT/boot/efi/EFI/%{efidir}/grub.cfg
ln -s ../boot/efi/EFI/%{efidir}/grub.cfg $RPM_BUILD_ROOT%{_sysconfdir}/%{name}-efi.cfg

# Install ELF files modules and images were created from into
# the shadow root, where debuginfo generator will grab them from
find $RPM_BUILD_ROOT -name '*.mod' -o -name '*.img' |
while read MODULE
do
        BASE=$(echo $MODULE |sed -r "s,.*/([^/]*)\.(mod|img),\1,")
        # Symbols from .img files are in .exec files, while .mod
        # modules store symbols in .elf. This is just because we
        # have both boot.img and boot.mod ...
        EXT=$(echo $MODULE |grep -q '.mod' && echo '.elf' || echo '.exec')
        TGT=$(echo $MODULE |sed "s,$RPM_BUILD_ROOT,.debugroot,")
#        install -m 755 -D $BASE$EXT $TGT
done
install -m 755 %{grubefiname} $RPM_BUILD_ROOT/boot/efi/EFI/%{efidir}/%{grubefiname}
install -m 755 %{grubeficdname} $RPM_BUILD_ROOT/boot/efi/EFI/%{efidir}/%{grubeficdname}
# XCP-ng: Add fallback for when all boot entries fail
# (buggy UEFI implementation, NVRAM error, user error in configuring boot entries, etc... could all cause this)
mkdir -p $RPM_BUILD_ROOT/boot/efi/EFI/%{efibootdir}/
install -m 755 %{grubefiname} $RPM_BUILD_ROOT/boot/efi/EFI/%{efibootdir}/%{grubefibootname}
popd
%endif

make DESTDIR=$RPM_BUILD_ROOT install

# Ghost config file
install -d $RPM_BUILD_ROOT/boot/%{name}
touch $RPM_BUILD_ROOT/boot/%{name}/grub.cfg
ln -s ../boot/%{name}/grub.cfg $RPM_BUILD_ROOT%{_sysconfdir}/%{name}.cfg

# Install ELF files modules and images were created from into
# the shadow root, where debuginfo generator will grab them from
find $RPM_BUILD_ROOT -name '*.mod' -o -name '*.img' |
while read MODULE
do
        BASE=$(echo $MODULE |sed -r "s,.*/([^/]*)\.(mod|img),\1,")
        # Symbols from .img files are in .exec files, while .mod
        # modules store symbols in .elf. This is just because we
        # have both boot.img and boot.mod ...
        EXT=$(echo $MODULE |grep -q '.mod' && echo '.elf' || echo '.exec')
        TGT=$(echo $MODULE |sed "s,$RPM_BUILD_ROOT,.debugroot,")
#        install -m 755 -D $BASE$EXT $TGT
done

rm $RPM_BUILD_ROOT%{_infodir}/dir

# Defaults
mkdir ${RPM_BUILD_ROOT}%{_sysconfdir}/default
touch ${RPM_BUILD_ROOT}%{_sysconfdir}/default/grub
mkdir ${RPM_BUILD_ROOT}%{_sysconfdir}/sysconfig
ln -sf %{_sysconfdir}/default/grub \
    ${RPM_BUILD_ROOT}%{_sysconfdir}/sysconfig/grub

# Make selinux happy with exec stack binaries.
mkdir ${RPM_BUILD_ROOT}%{_sysconfdir}/prelink.conf.d/
cat << EOF > ${RPM_BUILD_ROOT}%{_sysconfdir}/prelink.conf.d/grub2.conf
# these have execstack, and break under selinux
-b /usr/bin/grub2-script-check
-b /usr/bin/grub2-mkrelpath
-b /usr/bin/grub2-fstest
-b /usr/sbin/grub2-bios-setup
-b /usr/sbin/grub2-probe
-b /usr/sbin/grub2-sparc64-setup
EOF

%clean    
rm -rf $RPM_BUILD_ROOT

%post
if [ "$1" = 1 ]; then
    /sbin/install-info --info-dir=%{_infodir} %{_infodir}/%{name}.info.gz || :
    /sbin/install-info --info-dir=%{_infodir} %{_infodir}/%{name}-dev.info.gz || :
fi

%triggerun -- grub2 < 1:1.99-4
# grub2 < 1.99-4 removed a number of essential files in postun. To fix upgrades
# from the affected grub2 packages, we first back up the files in triggerun and
# later restore them in triggerpostun.
# https://bugzilla.redhat.com/show_bug.cgi?id=735259

# Back up the files before uninstalling old grub2
mkdir -p /boot/grub2.tmp &&
mv -f /boot/grub2/*.mod \
      /boot/grub2/*.img \
      /boot/grub2/*.lst \
      /boot/grub2/device.map \
      /boot/grub2.tmp/ || :

%triggerpostun -- grub2 < 1:1.99-4
# ... and restore the files.
test ! -f /boot/grub2/device.map &&
test -d /boot/grub2.tmp &&
mv -f /boot/grub2.tmp/*.mod \
      /boot/grub2.tmp/*.img \
      /boot/grub2.tmp/*.lst \
      /boot/grub2.tmp/device.map \
      /boot/grub2/ &&
rm -r /boot/grub2.tmp/ || :

%preun
if [ "$1" = 0 ]; then
    /sbin/install-info --delete --info-dir=%{_infodir} %{_infodir}/%{name}.info.gz || :
    /sbin/install-info --delete --info-dir=%{_infodir} %{_infodir}/%{name}-dev.info.gz || :
fi

%files
%defattr(-,root,root,-)
%{_libdir}/grub/*-%{platform}/
%config(noreplace) %{_sysconfdir}/%{name}.cfg
%ghost %config(noreplace) /boot/%{name}/grub.cfg
%doc COPYING

%ifarch %{efiarchs}
%files efi
%defattr(-,root,root,-)
%{_libdir}/grub/%{grubefiarch}
%config(noreplace) %{_sysconfdir}/%{name}-efi.cfg
%dir /boot/efi/EFI/%{efidir}
%attr(0755,root,root) /boot/efi/EFI/%{efidir}/*.efi
%attr(0755,root,root) /boot/efi/EFI/%{efibootdir}/*.efi
%ghost %config(noreplace) /boot/efi/EFI/%{efidir}/grub.cfg
%doc COPYING
%endif

%files tools
%defattr(-,root,root,-)
%dir %{_libdir}/grub/
%dir %{_datarootdir}/grub/
%{_datarootdir}/grub/*
%{_sbindir}/%{name}-bios-setup
%{_sbindir}/%{name}-install
%{_sbindir}/%{name}-macbless
%{_sbindir}/%{name}-mkconfig
%{_sbindir}/%{name}-ofpathname
%{_sbindir}/%{name}-probe
%{_sbindir}/%{name}-reboot
%{_sbindir}/%{name}-set-default
%{_sbindir}/%{name}-sparc64-setup
%{_bindir}/%{name}-editenv
%{_bindir}/%{name}-file
%{_bindir}/%{name}-fstest
%{_bindir}/%{name}-glue-efi
%{_bindir}/%{name}-kbdcomp
%{_bindir}/%{name}-menulst2cfg
%{_bindir}/%{name}-mkfont
%{_bindir}/%{name}-mkimage
%{_bindir}/%{name}-mklayout
%{_bindir}/%{name}-mknetdir
%{_bindir}/%{name}-mkpasswd-pbkdf2
%{_bindir}/%{name}-mkrelpath
%ifnarch %{sparc}
%{_bindir}/%{name}-mkrescue
%endif
%{_bindir}/%{name}-mkstandalone
%{_bindir}/%{name}-render-label
%{_bindir}/%{name}-script-check
%{_bindir}/%{name}-syslinux2cfg
%{_sysconfdir}/bash_completion.d/grub
%{_sysconfdir}/prelink.conf.d/grub2.conf
%attr(0700,root,root) %dir %{_sysconfdir}/grub.d
%config %{_sysconfdir}/grub.d/??_*
%{_sysconfdir}/grub.d/README
%attr(0644,root,root) %ghost %config(noreplace) %{_sysconfdir}/default/grub
%{_sysconfdir}/sysconfig/grub
%dir /boot/%{name}
%{_infodir}/%{name}*
%doc COPYING INSTALL
%doc NEWS README
%doc THANKS TODO
%doc grub.html
%doc grub-dev.html docs/font_char_metrics.png
%{_mandir}/man1/*
%exclude %{_mandir}/man1/*syslinux2cfg.1*
%{_mandir}/man8/*

%changelog
* Mon Sep 23 2019 Ross Lagerwall <ross.lagerwall@citrix.com> - 2.02-3.0.0
- CA-322681: ns8250: Wait a short while before draining the input buffer
