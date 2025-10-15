## Authentication

This one took a few days to sort out. Your ISU will need to be in a group applied to an authentication policy that allows username password access. I created a user based security group with a name of AllowBasicAuth and then also create an authentication rule with the same name. It included the AllowBasicAuth user based security group. I than allow only username password access. If this is new to you I would start by running **"Activate all Pending Authentication Policy Changes"**. In there select the policy to work on and see if you have something that will work. If not click on the pop-up icon at the end of the **Authentication Policy** name and then edit it. I would then add a policy similar to described above, you'll need to work with your security person to get this set up.

## Verificaiton

I discovered this was the issue by reviewing sign-on information for my ISU account. View system account sign-ons. I found this by clicking on the lego to the right of the ISU username while viewing the ISSG security group the use has access to for access the RaaS items.