%global package_speccommit 5a0928cc7e5b0d008bdfdebdd80db2e839948011
%global usver 2.12
%global xsver 14
%global xsrel %{xsver}%{?xscount}%{?xshash}
# This package calls binutils components directly and would need to pass
# in flags to enable the LTO plugins
# Disable LTO
%global _lto_cflags %{nil}

%undefine _hardened_build

%global package_srccommit 0e367796c0f41cb77562aa30282d85d0d2b3480a
%global package_suffix 0e367796c0f4

# Modules always contain just 32-bit code
%define _libdir %{_exec_prefix}/lib

%global grubefiarch %{_arch}-efi
%global grubefiname grubx64.efi
%global efidir xenserver

%undefine _missing_build_ids_terminate_build

# submodule gnulib
%define gnulib_cset stable-202201
%define gnulib_path gnulib

Name:           grub
Epoch:          0
Version:        2.12
Release: %{?xsrel}%{?dist}
Summary:        Bootloader with support for Linux, Multiboot and more

Group:          System Environment/Base
License:        GPLv3+
URL:            http://www.gnu.org/software/grub/
Source0: grub-2.12-0e367796c0f4.tar.gz
Source1: gnulib.tar.gz
Source2: sbat.csv.in
Patch0: 00045-efi-disallow-fallback-to-legacy-Linux-loader-when-shim.patch
Patch1: 0001-efi-Add-EFI-string-comparison-function.patch
Patch2: 0002-efi-Add-filesystem-definitions.patch
Patch3: 0003-loader-efi-linux-Make-device-handle-and-path-settabl.patch
Patch4: 0004-loader-efi-linux-Allocate-device-path-on-the-stack.patch
Patch5: 0005-loader-efi-linux-Set-device-path-when-loading-via-sh.patch
Patch6: 0006-sb-Verify-Xen-hypevisor-and-don-t-verify-modules.patch
Patch7: 0007-Add-xen_boot-module-for-x86_64_efi.patch
Patch8: wait-before-drain.patch

BuildRequires:  flex bison binutils python
BuildRequires:  ncurses-devel xz-devel
BuildRequires:  libusb1-devel
BuildRequires:  %{_exec_prefix}/lib64/crt1.o glibc-static
BuildRequires:  autoconf automake device-mapper-devel
BuildRequires:  gettext-devel git
BuildRequires:  texinfo
BuildRequires:  xssign-macros
%{?_cov_buildrequires}

# Although there's no grub-efi rpm, we still provide grub-efi for install-image
Provides: %{name}-efi = %{epoch}:%{version}-%{release}

ExcludeArch:    s390 s390x %{arm} %{ix86}

%description
The GRand Unified Bootloader (GRUB) is a highly configurable and customizable
bootloader with modular architecture.  It support rich varietyof kernel formats,
file systems, computer architectures and hardware devices.
This package provides support for EFI systems.


%prep
%autosetup -p1
tar -zxf %{SOURCE1}
%{?_cov_prepare}

%build

./bootstrap
%configure \
    CFLAGS="$(echo $RPM_OPT_FLAGS | sed \
        -e 's/-O. /-Os /g' \
        -e 's/-fstack-protector[[:alpha:]-]\+//g' \
        -e 's/-fstack-protector//g' \
        -e 's/--param=ssp-buffer-size=4//g' \
        -e 's/-mregparm=3/-mregparm=4/g' \
        -e 's/-fexceptions//g' \
        -e 's/-fasynchronous-unwind-tables//g' \
        -e 's/-m64//g' \
        -e 's/-fcf-protection//g' \
        -e 's/^/ -fno-strict-aliasing /' \
        -e 's/^/ -fno-stack-protector /' \
                )"                                              \
    TARGET_LDFLAGS=-static \
        --with-platform=efi \
    --with-grubdir=%{name} \
        --program-transform-name=s,grub,%{name}, \
    --disable-grub-mount \
    --disable-werror
%{?_cov_wrap} make %{?_smp_mflags}

sed -e 's/@@VERSION@@/%{version}/g' -e 's/@@RELEASE@@/%{release}/g' < %{SOURCE2} > sbat.csv

# The following modules are needed for UEFI booting and are included in the
# GRUB UEFI binary.
# Note that these modules may have dependencies on other modules so this is
# not the entire list of included modules, only the direct dependencies.
GRUB_MODULES="\
    boot            $(: Needed to boot) \
    chain           $(: Needed for chainloading, e.g. during testing) \
    configfile      $(: Load config files) \
    efifwsetup      $(: Allow rebooting into the firmware setup menu) \
    efinet          $(: Allow GRUB to load files from the network when PXE booting) \
    ext2            $(: Load xen, kernel from /boot) \
    fat             $(: Load grub.cfg from ESP) \
    gzio            $(: Decompress xen.gz) \
    halt            $(: Allow shutting down from GRUB) \
    iso9660         $(: Load xen, kernel from ISO during installation) \
    loadenv         $(: Load an environment file, used during upgrade) \
    minicmd         $(: Provides a few basic GRUB commands) \
    multiboot2      $(: Used for booting xen.gz) \
    normal          $(: Basic GRUB functionality) \
    part_gpt        $(: Allow reading GPT partition tables) \
    reboot          $(: Allow rebooting from GRUB) \
    search          $(: Support for the search command to set the root variable as needed) \
    search_fs_file  $(: Used for setting the root based on the presence of a file when installing from USB) \
    search_label    $(: Used for setting the root on an installed system based on a filesystem label) \
    serial          $(: Configure the serial console) \
    test            $(: Provides the test command which is used to evaluate an expression) \
    tftp            $(: Allow GRUB to load files from a TFTP server when PXE booting) \
    xen_boot        $(: Used for booting xen.efi) \
"
./grub-mkimage -O %{grubefiarch} -o %{grubefiname} -p /EFI/%{efidir} \
        -d grub-core --sbat sbat.csv ${GRUB_MODULES}
%sign -c GRUB_SIGN_KEY_XS9 -i %{grubefiname} -o %{grubefiname}.signed


%install
set -e

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
install -m 755 %{grubefiname}.signed $RPM_BUILD_ROOT/boot/efi/EFI/%{efidir}/%{grubefiname}

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

rm -rf $RPM_BUILD_ROOT%{_infodir}/dir

# Remove grub files
rm -rf $RPM_BUILD_ROOT%{_libdir}/grub
rm -rf $RPM_BUILD_ROOT%{_sysconfdir}/%{name}.cfg
rm -rf $RPM_BUILD_ROOT/boot/%{name}/grub.cfg

# Remove tools files
rm -rf $RPM_BUILD_ROOT%{_datarootdir}/grub/*
rm -rf $RPM_BUILD_ROOT%{_sbindir}/%{name}-bios-setup
rm -rf $RPM_BUILD_ROOT%{_sbindir}/%{name}-install
rm -rf $RPM_BUILD_ROOT%{_sbindir}/%{name}-macbless
rm -rf $RPM_BUILD_ROOT%{_sbindir}/%{name}-mkconfig
rm -rf $RPM_BUILD_ROOT%{_sbindir}/%{name}-ofpathname
rm -rf $RPM_BUILD_ROOT%{_sbindir}/%{name}-probe
rm -rf $RPM_BUILD_ROOT%{_sbindir}/%{name}-reboot
rm -rf $RPM_BUILD_ROOT%{_sbindir}/%{name}-set-default
rm -rf $RPM_BUILD_ROOT%{_sbindir}/%{name}-sparc64-setup
rm -rf $RPM_BUILD_ROOT%{_bindir}/%{name}-file
rm -rf $RPM_BUILD_ROOT%{_bindir}/%{name}-fstest
rm -rf $RPM_BUILD_ROOT%{_bindir}/%{name}-glue-efi
rm -rf $RPM_BUILD_ROOT%{_bindir}/%{name}-kbdcomp
rm -rf $RPM_BUILD_ROOT%{_bindir}/%{name}-menulst2cfg
rm -rf $RPM_BUILD_ROOT%{_bindir}/%{name}-mkimage
rm -rf $RPM_BUILD_ROOT%{_bindir}/%{name}-mklayout
rm -rf $RPM_BUILD_ROOT%{_bindir}/%{name}-mknetdir
rm -rf $RPM_BUILD_ROOT%{_bindir}/%{name}-mkpasswd-pbkdf2
rm -rf $RPM_BUILD_ROOT%{_bindir}/%{name}-mkrelpath
rm -rf $RPM_BUILD_ROOT%{_bindir}/%{name}-mkrescue
rm -rf $RPM_BUILD_ROOT%{_bindir}/%{name}-mkstandalone
rm -rf $RPM_BUILD_ROOT%{_bindir}/%{name}-render-label
rm -rf $RPM_BUILD_ROOT%{_bindir}/%{name}-script-check
rm -rf $RPM_BUILD_ROOT%{_bindir}/%{name}-syslinux2cfg
rm -rf $RPM_BUILD_ROOT%{_datadir}/bash-completion/completions
rm -rf $RPM_BUILD_ROOT%{_sysconfdir}/prelink.conf.d/grub2.conf
rm -rf $RPM_BUILD_ROOT%{_sysconfdir}/grub.d/*
rm -rf $RPM_BUILD_ROOT%{_sysconfdir}/default/grub
rm -rf $RPM_BUILD_ROOT%{_sysconfdir}/sysconfig/grub
rm -rf $RPM_BUILD_ROOT%{_infodir}/%{name}*
rm -rf $RPM_BUILD_ROOT%{_mandir}/man1/*
rm -rf $RPM_BUILD_ROOT%{_mandir}/man8/*

%{?_cov_install}

%files
%defattr(-,root,root,-)
%{_bindir}/%{name}-editenv
%config(noreplace) %{_sysconfdir}/%{name}-efi.cfg
%dir /boot/efi/EFI/%{efidir}
%attr(0755,root,root) /boot/efi/EFI/%{efidir}/*.efi
%ghost %config(noreplace) /boot/efi/EFI/%{efidir}/grub.cfg
%doc COPYING

%{?_cov_results_package}

%changelog
* Wed Oct 08 2025 Ross Lagerwall <ross.lagerwall@citrix.com> - 2.12-14
- CP-47917: Re-sign with new key

* Tue Sep 16 2025 Ross Lagerwall <ross.lagerwall@citrix.com> - 2.12-13
- CP-309737: Remove fallback path
- Remove obsolete cruft

* Mon Aug 18 2025 Ross Lagerwall <ross.lagerwall@citrix.com> - 2.12-12
- CP-308091: Drop old NX patches
- Remove duplicate grub_file_open call

* Wed Aug 06 2025 Ross Lagerwall <ross.lagerwall@citrix.com> - 2.12-11
- CA-414792: Fix issues with xen_boot unload

* Tue Jul 29 2025 Ross Lagerwall <ross.lagerwall@citrix.com> - 2.12-10
- CP-308937: Add xen_boot module for booting xen.efi
- CP-308937: Remove multiboot PE support

* Tue Jul 29 2025 Alex Brett <alex.brett@cloud.com> - 2.12-9
- CP-309224: Add chain module

* Thu Jul 10 2025 Alex Brett <alex.brett@cloud.com> - 2.12-8
- CA-405659: Include test module in grub image

* Fri Jul 04 2025 Ross Lagerwall <ross.lagerwall@citrix.com> - 2.12-7
- Update SBAT email address

* Tue Jun 24 2025 Ross Lagerwall <ross.lagerwall@citrix.com> - 2.12-6
- CP-308443: Update to grub development snapshot from 2025-06-24

* Wed May 21 2025 Frediano Ziglio <frediano.ziglio@cloud.com> - 2.12-5
- CP-308117: Rebuild due to signature issue

* Thu Apr 17 2025 Ross Lagerwall <ross.lagerwall@citrix.com> - 2.12-4
- CP-49469: Depend on python3-xssign

* Fri Apr 11 2025 Ross Lagerwall <ross.lagerwall@citrix.com> - 2.12-3
- CP-45134: Add Secure Boot support

* Wed Jan 22 2025 Alex Brett <alex.brett@cloud.com> - 2.12-2
- CA-405116: Fix build in the absence of tools to make info docs

* Thu Jan 09 2025 Lin Liu <Lin.Liu01@cloud.com> - 2.12-1.0.2
- Package grub-editenv and remove lib files

* Mon Nov 11 2024 Stephen Cheng <stephen.cheng@cloud.com> - 2.12-1.0.1
- CP-50676: Remove gettext
- CP-50552: Remove BIOS support from grub

* Wed Aug 14 2024 Gerald Elder-Vass <gerald.elder-vass@cloud.com> - 2.12-1.0.0
- Update to grub 2.12 and gnulib_cset stable-202201

* Thu May 30 2024 Deli Zhang <deli.zhang@cloud.com> - 2.06-4.0.4
- CP-46111: Remove build require freetype-devel

* Thu Apr 11 2024 Frediano Ziglio <frediano.ziglio@cloud.com> - 2.06-4.0.3
- CP-47745: compatibilities for XS9, optimize back some code

* Wed May 17 2023 Ross Lagerwall <ross.lagerwall@citrix.com> - 2.06-4.0.2
- HP-1153: always enforce requested allocation alignment

* Mon Feb 21 2022 Ross Lagerwall <ross.lagerwall@citrix.com> - 2.06-4.0.1
- CP-38416: Enable static analysis

* Fri Jul 02 2021 Igor Druzhinin <igor.druzhinin@citrix.com> - 2.06-4.0.0
- CP-37232: Updated Grub to 2.06

* Tue Jun 29 2021 Benjamin Reis <benjamin.reis@vates.fr> - 2.02-3.0.2
- Add EFI fallback file (`EFI/BOOT/BOOTX64.EFI`) for when all boot entries fail

* Fri Dec 04 2020 Ross Lagerwall <ross.lagerwall@citrix.com> - 2.02-3.0.1
- CP-35517: Rebuild for koji

* Mon Sep 23 2019 Ross Lagerwall <ross.lagerwall@citrix.com> - 2.02-3.0.0
- CA-322681: ns8250: Wait a short while before draining the input buffer
