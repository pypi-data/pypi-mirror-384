# https://vagrant-libvirt.github.io/vagrant-libvirt/installation.html#ubuntu-1810-debian-9-and-up

set -e

sudo apt-get purge vagrant-libvirt
sudo apt-mark hold vagrant-libvirt
sudo apt-get install -y qemu libvirt-daemon-system libvirt-dev ebtables libguestfs-tools
sudo apt-get install -y vagrant ruby-fog-libvirt

gem sources --add https://gems.ruby-china.com/ --remove https://rubygems.org/
# gem sources -l

# vagrant plugin install --plugin-clean-sources --plugin-source https://gems.ruby-china.com/ vagrant-libvirt
vagrant plugin install vagrant-libvirt
# vagrant plugin install vagrant-scp
## vagrant scp somefile [vm_name]:/home/vagrant/somefile

## uninstall
#sudo apt-get remove --purge libvirt-bin kvm qemu qemu-system-x86
#sudo apt-get purge libvirt* kvm qemu*
#sudo apt-get autoremove
