#!/usr/bin/env bash
set -euo pipefail
VER=${1:-1.0.0}
mkdir -p ~/rpmbuild/{BUILD,RPMS,SOURCES,SPECS,SRPMS}
cp dist/OrganizadorArquivos ~/rpmbuild/SOURCES/
cat > ~/rpmbuild/SPECS/organizador-arquivos.spec <<EOF
Name: organizador-arquivos
Version: $VER
Release: 1
Summary: Organizador de Arquivos
License: MIT
BuildArch: x86_64

%description
Organiza arquivos por tipo em pastas.

%install
mkdir -p %{buildroot}/usr/bin
install -m 755 %{_sourcedir}/OrganizadorArquivos %{buildroot}/usr/bin/OrganizadorArquivos
ln -sf OrganizadorArquivos %{buildroot}/usr/bin/organizador-arquivos

%files
/usr/bin/OrganizadorArquivos
/usr/bin/organizador-arquivos
EOF
rpmbuild -bb ~/rpmbuild/SPECS/organizador-arquivos.spec
find ~/rpmbuild/RPMS -name '*.rpm' -exec cp {} . \;
