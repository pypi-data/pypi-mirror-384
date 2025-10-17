#
# curlInterface: Simple Web Access
#
# Reading the declaration part of the package.
#

if not LoadKernelExtension("curlInterface", "curl") then
  Error("failed to load the curlInterface package kernel extension");
fi;

# work around a bug in some PackageManager versions, see
# <https://github.com/gap-packages/PackageManager/pull/100>.
Unbind(DownloadURL);

ReadPackage( "curlInterface", "gap/curl.gd");
