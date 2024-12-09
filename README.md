# doh-proxy-mikrotik
DoH proxy for Mikrotik. The original DoH implementation is not stable for me, so I'll keep the container implementation.

Install builders for the required architecture (arm or arm64):<br>
`docker run --privileged --rm tonistiigi/binfmt --install all`

Build for arm:<br>
`docker buildx build --no-cache --platform linux/arm/v6 -t dns .`

Build for arm64:<br>
`docker buildx build --no-cache --platform linux/arm64/v8 -t dns .`

Pack the container into an archive:<br>
`docker save dns -o dns.tar`

Copy the .tar to the Mikrotik

Create an interface for the container:<br>
`/interface/veth/add address=192.168.1.2/24 gateway=192.168.1.1 name=veth-doh comment="DoH container"`

Unzip the container and save it to a USB drive:<br>
`/container/add file=dns.tar interface=veth-doh root-dir=usb1/Containers/doh-mikrotik workdir=/root start-on-boot=yes logging=yes comment="DoH container"`

Creating a bridge:<br>
`/interface/bridge/add name=container-doh`

Create a network for the created bridge:<br>
`/ip/address/add address=192.168.1.1/24 network=192.168.1.0 interface=container-doh comment="DoH container"`

Add the container interface to the created bridge:<br>
`/interface/bridge/port add bridge=container-doh interface=veth-doh`

Making a masquerade for the created network:<br>
`/ip/firewall/nat add chain=srcnat src-address=192.168.1.0/24 out-interface={{you-WAN}} action=masquerade comment="DoH container"`

In IP -> DNS you can delete all previously added DNS and DoH servers and specify the address of the created container: `192.168.1.2`