%define version @@VERSION@@
%define release @@RELEASE@@
%define revision @@REVISION@@
%define debug_package %{nil}
%define SRC_DIR percona-agent-%{version}
%define CWD %{_builddir}/%{SRC_DIR}
%define VENDOR_DIR %{CWD}/vendor
%define service_name percona-agent
%define basedir /usr/local/percona

%bcond_with systemd
#
%if %{with systemd}
  %define systemd 1
%else
  %if 0%{?rhel} > 6
    %define systemd 1
  %else
    %define systemd 0
  %endif
%endif

Name:         percona-agent
Version:      %{version}
Release:      %{release}%{?dist}
Summary:      Percona Agent for Percona Cloud Tools
License:      GPL-3.0+
Source0:       %{SRC_DIR}.tar.gz
Source1:      percona-agent.service
Group:        System Environment/Base
BuildRoot:    %{_tmppath}/%{name}-%{version}-%{release}-%{_arch}
Packager:     Percona Development Team <mysqldev@percona.com>
BuildRequires:  golang >= 1.3, git, mercurial
%if 0%{?systemd}
BuildRequires:  systemd
Requires(post):   systemd
Requires(preun):  systemd
Requires(postun): systemd
%else
Requires(post):   /sbin/chkconfig
Requires(preun):  /sbin/chkconfig
Requires(preun):  /sbin/service
%endif

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

%if 0%{?systemd}
%{__install} -D -m 0644 %{SOURCE1} %{buildroot}/%{_unitdir}/percona-agent.service
%else
%{__install} -D -m 755 %{CWD}/install/percona-agent %{buildroot}/%{_sysconfdir}/init.d/percona-agent
%endif

# create symlinks for binaries
ln -s %{buildroot}/usr/local/percona/percona-agent/bin/percona-agent %{buildroot}/%{_sbindir}/percona-agent
ln -s %{buildroot}/usr/local/percona/percona-agent/bin/percona-agent-installer %{buildroot}/%{_sbindir}/percona-agent-installer

%files
%doc COPYING README.md Changelog Authors
%attr(755, root, root) /usr/local/percona/percona-agent/bin/percona-agent
%attr(755, root, root) /usr/local/percona/percona-agent/bin/percona-agent-installer
%attr(755, root, root) %{_sysconfdir}/init.d/percona-agent

%post
%if 0%{?systemd}
  if [ -x %{_bindir}/systemctl ] ; then
    %{_bindir}/systemctl enable percona-agent >/dev/null 2>&1
  fi
%else
  # Add the init script but do not start agent right away
  if [ -x /sbin/chkconfig ] ; then
    /sbin/chkconfig --add percona-agent
  # use insserv for older SuSE Linux versions
  elif [ -x /sbin/insserv ] ; then
    /sbin/insserv %{_sysconfdir}/init.d/percona-agent
  fi
%endif

# On initial installation show message about configuring and starting
if [ $1 = 1 ] ; then
    echo ""
    echo "================================================================================"
	echo "Percona Agent is installed but not configured and started."
    echo ""
	echo "Run the following command with root permissions to configure (replace values as needed):"
	echo "  percona-agent-installer -mysql-user=root -mysql-pass=mysql_root_pass -api-key=your_key_here"
    echo ""
	echo "To start the service run following:"
	echo "  service percona-agent start";
    echo "================================================================================"
    echo ""
fi

%postun
# Start Percona Agent after upgrade
%if 0%{?systemd}
%systemd_postun_with_restart percona-agent
%else
if [ $1 -ge 1 ] ; then
    if [ -x %{_sysconfdir}/init.d/percona-agent ] ; then
            %{_sysconfdir}/init.d/percona-agent start > /dev/null
    fi
fi
%endif

# If uninstall remove basedir
if [ $1 = 0 ] ; then
    rm -rf %{basedir}/%{service_name}
fi

%preun
%if 0%{?systemd}
    %systemd_preun percona-agent
%else
if [ $1 = 0 ] ; then
    # Stop Percona Agent before uninstalling it
    if [ -x %{_sysconfdir}/init.d/percona-agent ] ; then
            %{_sysconfdir}/init.d/percona-agent stop > /dev/null
            # Remove autostart of Percona Agent
            # use chkconfig on Enterprise Linux and newer SuSE releases
            if [ -x /sbin/chkconfig ] ; then
                    /sbin/chkconfig --del percona-agent
            # For older SuSE Linux versions
            elif [ -x /sbin/insserv ] ; then
                    /sbin/insserv -r %{_sysconfdir}/init.d/percona-agent
            fi
    fi
fi
%endif

%changelog
* Fri Sep 26 2014 Tomislav Plavcic <tomislav.plavcic@percona.com>

- initial packaging
