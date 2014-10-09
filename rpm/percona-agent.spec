%define version @@VERSION@@
%define release @@RELEASE@@
%define revision @@REVISION@@
%define SRC_DIR percona-agent-%{version}
%define CWD %{_builddir}/%{SRC_DIR}
%define VENDOR_DIR %{CWD}/vendor

Name:         percona-agent
Version:      %{version}
Release:      %{release}%{?dist}
Summary:      Percona Agent for Percona Cloud Tools
License:      GPL-3.0+
Source:       %{SRC_DIR}.tar.gz
Group:        System Environment/Base
BuildRoot:    %{_tmppath}/%{name}-%{version}-%{release}-%{_arch}
Packager:     Percona Development Team <mysqldev@percona.com>
BuildRequires:  golang >= 1.3, git, mercurial

%description
This is percona-agent for Percona Cloud Tools. It's a real-time client-side 
agent written in Go which implements the various services provided by 
Percona Cloud Tools (PCT). You need a PCT account to install and use the agent.

%clean
%{__rm} -rf %{buildroot}

%prep
%setup -n %{SRC_DIR}

%build
%{__rm} -rf %{buildroot}
export GOPATH=%{VENDOR_DIR}:%{CWD}

# Create a symlink so that build util finds a go package
mkdir -p src/github.com/percona
ln -s %{CWD} src/github.com/percona/percona-agent

# Build a util for downloading dependencies
(cd build/agent-build && go build)

# Download dependencies
(cd build/agent-build && ./agent-build -build=false)

# Build percona-agent
(cd bin/percona-agent && go build -ldflags "-X github.com/percona/percona-agent/agent.REVISION %{revision}")

# Check that bin was compiled with pkgs from vendor dir
strings bin/percona-agent/percona-agent | grep "%{VENDOR_DIR}/src/github.com/percona/cloud-protocol" || exit 1

# Build percona-agent-installer
(cd bin/percona-agent-installer && go build)

%install
%{__install} -D -m 755 %{CWD}/bin/percona-agent/percona-agent %{buildroot}/usr/local/percona/percona-agent/bin/percona-agent
%{__install} -D -m 755 %{CWD}/bin/percona-agent-installer/percona-agent-installer %{buildroot}/usr/local/percona/percona-agent/bin/percona-agent-installer
%{__install} -D -m 755 %{CWD}/install/percona-agent %{buildroot}/%{_sysconfdir}/init.d/percona-agent

%files
%doc COPYING README.md Changelog Authors
%attr(755, root, root) /usr/local/percona/percona-agent/bin/percona-agent
%attr(755, root, root) /usr/local/percona/percona-agent/bin/percona-agent-installer
%attr(755, root, root) %{_sysconfdir}/init.d/percona-agent

%changelog
* Fri Sep 26 2014 Tomislav Plavcic <tomislav.plavcic@percona.com>

- initial packaging
