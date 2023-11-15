#
# etcrebase
# Copyright (C) 2023  Eugenio Paolantonio <me@medesimo.eu>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#

%{?sle15_python_module_pythons}
Name:           python-etcrebase
Version:        0.0.2
Release:        0
Summary:        Rebases a new /etc with existing changes from a different installation
License:        GPL-2.0+
URL:            https://github.com/g7/etcrebase
Source0:        %{name}-%version.tar.xz
BuildRequires:  %{python_module setuptools}
Requires:       etcrebase-configs
Requires(post): update-alternatives
Requires(postun):update-alternatives
BuildArch:      noarch

%python_subpackages

%description
etcrebase is a tool that allows to rebase configuration changes from an /etc
directory to another.

It's only useful for specific usecases, you probably don't need it.

Currently it implies running in an openSUSE MicroOS system, but it can be adapted
to work on other distributions as well.

%package -n etcrebase-configs
Summary:        Rebases a new /etc with existing changes from a different installation

%description -n etcrebase-configs
etcrebase is a tool that allows to rebase configuration changes from an /etc
directory to another.

It's only useful for specific usecases, you probably don't need it.

Currently it implies running in an openSUSE MicroOS system, but it can be adapted
to work on other distributions as well.
.
This package contains common configurations lists for etcrebase.

%prep
%autosetup -n python-etcrebase-%{version}

%build
%python_build

%install
%python_install
%python_clone -a %{buildroot}%{_bindir}/etcrebase
install -d %{buildroot}%{_datadir}/etcrebase
install -m 644 data/* %{buildroot}%{_datadir}/etcrebase

%post
%python_install_alternative etcrebase

%postun
%python_uninstall_alternative etcrebase

%files %{python_files}
%doc README.md
%license LICENCE
%python_alternative %{_bindir}/etcrebase
%{python_sitelib}/etcrebase/
%{python_sitelib}/etcrebase-%{version}*-info

%files -n etcrebase-configs
%dir %{_datadir}/etcrebase
%{_datadir}/etcrebase/*

%changelog
