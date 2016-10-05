#!/usr/bin/env python

import boto.ec2
import boto.ec2.elb
import boto.beanstalk
import re
import argparse

# Global Vars
aws_profile = ""
result = {}
inst_ko = []
search = ""
aws_lb = ""
aws_beanstalk = ""
region = "eu-west-1"

# Args
parser = argparse.ArgumentParser()
parser.add_argument("--profile", "-p", help='Profile name on your .aws/credentials file *optional*')
parser.add_argument("--region", "-r", help='Specify the region (default eu-west-1) *optional*')
parser.add_argument("--loadbalancer", "-l", help='String to search for an ELB names')
parser.add_argument("--beanstalk", "-b", help='String to search on beanstalk')
parser.add_argument("search", nargs="?", default="")
args = parser.parse_args()
if args.profile:
    aws_profile = str(args.profile)
if args.loadbalancer:
    aws_lb = str(args.loadbalancer)
if args.beanstalk:
    aws_beanstalk = str(args.beanstalk)
if args.search:
    search = str(args.search)
if args.region:
    region = str(args.region)

# Connect
try:
    connection_ec2 = boto.ec2.connect_to_region(region, profile_name=aws_profile)
    connection_elb = boto.ec2.elb.connect_to_region(region, profile_name=aws_profile)
    connection_bst = boto.beanstalk.connect_to_region(region, profile_name=aws_profile)
    my_instances = connection_ec2.get_all_instances()
except:
    connection_ec2 = boto.ec2.connect_to_region(region)
    connection_elb = boto.ec2.elb.connect_to_region(region)
    connection_bst = boto.beanstalk.connect_to_region(region)
    my_instances = connection_ec2.get_all_instances()

#Color
class bcolors:
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'

#Give ID return IP
def find_inst_ip(inst_id):
    for res in my_instances:
        for inst in res.instances:
            if inst_id in str(inst):
                if inst_id in str(inst_ko):
                    return bcolors.RED + str(inst.private_ip_address) + bcolors.ENDC
                else:
                    return inst.private_ip_address


def find_elb(my_tag):
    n = ""
    all_elb = connection_elb.get_all_load_balancers()
    for my_elb in all_elb:
        if re.search(my_tag, str(my_elb), re.IGNORECASE):
            result[my_elb] = []
            inst_health = my_elb.get_instance_health()
            for i in inst_health:
                if re.search("InService", str(i)):
                    n = re.search('[a-z]\-([a-z]|[0-9])*', str(i))
                    result[my_elb].append(n.group(0))
                else:
                    n = re.search('[a-z]\-([a-z]|[0-9])*', str(i))
                    inst_ko.append(n.group(0))
                    result[my_elb].append(n.group(0))
    if result == {} and inst_ko == []:
        print bcolors.RED + "Pas d'ELB correspondant" + bcolors.ENDC
    i = 0
    for k, v in result.iteritems():
        print bcolors.BLUE + str(k) + bcolors.ENDC
        for i in v:
            print bcolors.GREEN + str(find_inst_ip(i)) + bcolors.ENDC,
        print "\n"


def find_ec2(my_tag):
    for instance in my_instances:        
        if (my_tag in instance.instances[0].private_ip_address or my_tag.lower() in instance.instances[0].tags['Name'].lower()) and "Name" in instance.instances[0].tags:
            print bcolors.GREEN + str(instance.instances[0].tags['Name']) + bcolors.ENDC
            if "running" in str(instance.instances[0]._state):
                print bcolors.GREEN + str(instance.instances[0].private_ip_address) + ":" + bcolors.ENDC
            else:
                print bcolors.RED + str(instance.instances[0].private_ip_address) + ":" + bcolors.ENDC
            print bcolors.BLUE + "Region: " + bcolors.ENDC + str(instance.instances[0]._placement) + bcolors.BLUE + "               State: " + bcolors.ENDC + str(instance.instances[0]._state)
            print bcolors.BLUE + "Id: " + bcolors.ENDC + str(instance.instances[0].id) + bcolors.BLUE + "                   Image: " + bcolors.ENDC + str(instance.instances[0].image_id)
            print bcolors.BLUE + "Launch: " + bcolors.ENDC + (instance.instances[0].launch_time) + bcolors.BLUE + " Type: " + bcolors.ENDC + str(instance.instances[0].instance_type)
            print ""
        else:
            pass

def find_bs(name_bs):
    envs = (e for e in
            connection_bst.describe_environments()
            ['DescribeEnvironmentsResponse']
            ['DescribeEnvironmentsResult']
            ['Environments']
            )
    for env in envs:
        resources = (
            connection_bst.describe_environment_resources(
                environment_name=env['EnvironmentName']
            )
            ['DescribeEnvironmentResourcesResponse']
            ['DescribeEnvironmentResourcesResult']
            ['EnvironmentResources']
        )
        if re.search(name_bs, str(env), re.IGNORECASE):
            if env['Status'] == 'Ready' and  env['Health'] == 'Green':
                print bcolors.GREEN + str(env['EnvironmentName']) + ":" + bcolors.ENDC
            else:
                print bcolors.YELLOW + str(env['EnvironmentName']) + ":" + bcolors.ENDC
            if resources['LoadBalancers'] != []:
                print bcolors.BLUE + "ELB: " + bcolors.ENDC + str(resources['LoadBalancers'][0]['Name'])

            liste_inst = ""
            for id in resources['Instances']:
                liste_inst += str(id['Id'])
                liste_inst += "  "
            print bcolors.BLUE + "ec2: " + bcolors.ENDC + str(liste_inst)


def main():
    ipv4 = re.compile("^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$")
    if aws_lb:
        if aws_lb == "@":
            find_elb("")
        else:
            find_elb(aws_lb)

    elif aws_beanstalk:
        if aws_beanstalk == "@":
            find_bs("")
        else:
            find_bs(aws_beanstalk)
    if aws_lb == "" and aws_beanstalk =="":
        find_ec2(search)

if __name__ == "__main__":
    main()
