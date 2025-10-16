load ./library.bats

setup_file() {
	echo "********************************************" >&3
	echo "Running tests in $BATS_TEST_FILENAME" >&3
	echo "********************************************" >&3

	[ -e ./rhjira ] && rm -f ./rhjira
	cp ../bin/rhjira .

	export TESTOUTPUT=${BATS_FILE_TMPDIR}/full.out
	./rhjira dump --showcustomfields --showemptyfields RHEL-56971 >& $TESTOUTPUT
}

@test "Release Date_customfield_12322243" {
	run grepdumpdata "FIELD\[Release\ Date\|customfield_12322243\]:"
	check_status
}

@test "PX Impact Score_customfield_12322244" {
	run grepdumpdata "FIELD\[PX\ Impact\ Score\|customfield_12322244\]:"
	check_status
}

@test "SFDC Cases Open_customfield_12324540" {
	run grepdumpdata "FIELD\[SFDC\ Cases\ Open\|customfield_12324540\]:"
	check_status
}

@test "Staffing_customfield_12322240" {
	run grepdumpdata "FIELD\[Staffing\|customfield_12322240\]:"
	check_status
}

@test "Gating Tests_customfield_12322241" {
	run grepdumpdata "FIELD\[Gating\ Tests\|customfield_12322241\]:"
	check_status
}

@test "Resolution_resolution" {
	run grepdumpdata "FIELD\[Resolution\|resolution\]:"
	check_status
}

@test "SVN / CVS Isolated Branch_customfield_12310022" {
	run grepdumpdata "FIELD\[SVN\ /\ CVS\ Isolated\ Branch\|customfield_12310022\]:"
	check_status
}

@test "Support Case Reference_customfield_12310021" {
	run grepdumpdata "FIELD\[Support\ Case\ Reference\|customfield_12310021\]:"
	check_status
}

@test "Percent complete_customfield_12314741" {
	run grepdumpdata "FIELD\[Percent\ complete\|customfield_12314741\]:"
	check_status
}

@test "Development_customfield_12314740" {
	run grepdumpdata "FIELD\[Development\|customfield_12314740\]:"
	check_status
}

@test "Fix Build_customfield_12312442" {
	run grepdumpdata "FIELD\[Fix\ Build\|customfield_12312442\]:"
	check_status
}

@test "Contributors_customfield_12315950" {
	run grepdumpdata "FIELD\[Contributors\|customfield_12315950\]:"
	check_status
}

@test "Last Viewed_lastViewed" {
	run grepdumpdata "FIELD\[Last\ Viewed\|lastViewed\]:"
	check_status
}

@test "Business justification_customfield_12325642" {
	run grepdumpdata "FIELD\[Business\ justification\|customfield_12325642\]:"
	check_status
}

@test "Internal Target Milestone_customfield_12321040" {
	run grepdumpdata "FIELD\[Internal\ Target\ Milestone\|customfield_12321040\]:"
	check_status
}

@test "Keywords_customfield_12323341" {
	run grepdumpdata "FIELD\[Keywords\|customfield_12323341\]:"
	check_status
}

@test "CDW qa_ack_customfield_12311244" {
	run grepdumpdata "FIELD\[CDW\ qa_ack\|customfield_12311244\]:"
	check_status
}

@test "CDW blocker_customfield_12311245" {
	run grepdumpdata "FIELD\[CDW\ blocker\|customfield_12311245\]:"
	check_status
}

@test "CDW pm_ack_customfield_12311242" {
	run grepdumpdata "FIELD\[CDW\ pm_ack\|customfield_12311242\]:"
	check_status
}

@test "CDW devel_ack_customfield_12311243" {
	run grepdumpdata "FIELD\[CDW\ devel_ack\|customfield_12311243\]:"
	check_status
}

@test "Epic Type_customfield_12313541" {
	run grepdumpdata "FIELD\[Epic\ Type\|customfield_12313541\]:"
	check_status
}

@test "Σ Original Estimate_aggregatetimeoriginalestimate" {
	run grepdumpdata "FIELD\[Σ\ Original\ Estimate\|aggregatetimeoriginalestimate\]:"
	check_status
}

@test "Target Release_customfield_12311240" {
	run grepdumpdata "FIELD\[Target\ Release\|customfield_12311240\]:"
	check_status
}

@test "CDW release_customfield_12311241" {
	run grepdumpdata "FIELD\[CDW\ release\|customfield_12311241\]:"
	check_status
}

@test "Affects_customfield_12310031" {
	run grepdumpdata "FIELD\[Affects\|customfield_12310031\]:"
	check_status
}

@test "Linked Issues_issuelinks" {
	run grepdumpdata "FIELD\[Linked\ Issues\|issuelinks\]:"
	check_status
}

@test "Assignee_assignee" {
	run grepdumpdata "FIELD\[Assignee\|assignee\]:"
	check_status
}

@test "CDW exception_customfield_12311246" {
	run grepdumpdata "FIELD\[CDW\ exception\|customfield_12311246\]:"
	check_status
}

@test "Annual Time Savings_customfield_12326941" {
	run grepdumpdata "FIELD\[Annual\ Time\ Savings\|customfield_12326941\]:"
	check_status
}

@test "QE Priority_customfield_12319294" {
	run grepdumpdata "FIELD\[QE\ Priority\|customfield_12319294\]:"
	check_status
}

@test "Affected Groups_customfield_12319293" {
	run grepdumpdata "FIELD\[Affected\ Groups\|customfield_12319293\]:"
	check_status
}

@test "CMDB ID_customfield_12324640" {
	run grepdumpdata "FIELD\[CMDB\ ID\|customfield_12324640\]:"
	check_status
}

@test "EBS Account Number_customfield_12326942" {
	run grepdumpdata "FIELD\[EBS\ Account\ Number\|customfield_12326942\]:"
	check_status
}

@test "Work Type_customfield_12320040" {
	run grepdumpdata "FIELD\[Work\ Type\|customfield_12320040\]:"
	check_status
}

@test "ProdDocsReview-CCS_customfield_12322343" {
	run grepdumpdata "FIELD\[ProdDocsReview\-CCS\|customfield_12322343\]:"
	check_status
}

@test "Annual Cost Savings/Avoidance_customfield_12326940" {
	run grepdumpdata "FIELD\[Annual\ Cost\ Savings/Avoidance\|customfield_12326940\]:"
	check_status
}

@test "ProdDocsReview-QE_customfield_12322344" {
	run grepdumpdata "FIELD\[ProdDocsReview\-QE\|customfield_12322344\]:"
	check_status
}

@test "Strategic Relationship_customfield_12319295" {
	run grepdumpdata "FIELD\[Strategic\ Relationship\|customfield_12319295\]:"
	check_status
}

@test "ProdDocsReview-Dev_customfield_12322340" {
	run grepdumpdata "FIELD\[ProdDocsReview\-Dev\|customfield_12322340\]:"
	check_status
}

@test "SME_customfield_12319299" {
	run grepdumpdata "FIELD\[SME\|customfield_12319299\]:"
	check_status
}

@test "SLA Date_customfield_12326949" {
	run grepdumpdata "FIELD\[SLA\ Date\|customfield_12326949\]:"
	check_status
}

@test "PX Scheduling Request_customfield_12326947" {
	run grepdumpdata "FIELD\[PX\ Scheduling\ Request\|customfield_12326947\]:"
	check_status
}

@test "PX Technical Impact Notes_customfield_12326948" {
	run grepdumpdata "FIELD\[PX\ Technical\ Impact\ Notes\|customfield_12326948\]:"
	check_status
}

@test "Training Opportunity_customfield_12319290" {
	run grepdumpdata "FIELD\[Training\ Opportunity\|customfield_12319290\]:"
	check_status
}

@test "PX Impact Score_customfield_12326946" {
	run grepdumpdata "FIELD\[PX\ Impact\ Score\|customfield_12326946\]:"
	check_status
}

@test "MDM Account Reference_customfield_12326943" {
	run grepdumpdata "FIELD\[MDM\ Account\ Reference\|customfield_12326943\]:"
	check_status
}

@test "Testing Instructions_customfield_12319292" {
	run grepdumpdata "FIELD\[Testing\ Instructions\|customfield_12319292\]:"
	check_status
}

@test "Other Savings_customfield_12326944" {
	run grepdumpdata "FIELD\[Other\ Savings\|customfield_12326944\]:"
	check_status
}

@test "Training Opportunity Notes_customfield_12319291" {
	run grepdumpdata "FIELD\[Training\ Opportunity\ Notes\|customfield_12319291\]:"
	check_status
}

@test "Help Desk Ticket Reference_customfield_12310120" {
	run grepdumpdata "FIELD\[Help\ Desk\ Ticket\ Reference\|customfield_12310120\]:"
	check_status
}

@test "Doc Version/s_customfield_12314840" {
	run grepdumpdata "FIELD\[Doc\ Version/s\|customfield_12314840\]:"
	check_status
}

@test "Story Points_customfield_12310243" {
	run grepdumpdata "FIELD\[Story\ Points\|customfield_12310243\]:"
	check_status
}

@test "RH Private Keywords_customfield_12326953" {
	run grepdumpdata "FIELD\[RH\ Private\ Keywords\|customfield_12326953\]:"
	check_status
}

@test "Internal Whiteboard_customfield_12326950" {
	run grepdumpdata "FIELD\[Internal\ Whiteboard\|customfield_12326950\]:"
	check_status
}

@test "PX Technical Impact Notes_customfield_12325740" {
	run grepdumpdata "FIELD\[PX\ Technical\ Impact\ Notes\|customfield_12325740\]:"
	check_status
}

@test "Sub-Tasks_subtasks" {
	run grepdumpdata "FIELD\[Sub\-Tasks\|subtasks\]:"
	check_status
}

@test "GtmhubObjectID_customfield_12321140" {
	run grepdumpdata "FIELD\[GtmhubObjectID\|customfield_12321140\]:"
	check_status
}

@test "Onsite Date_customfield_12323440" {
	run grepdumpdata "FIELD\[Onsite\ Date\|customfield_12323440\]:"
	check_status
}

@test "Market_customfield_12326956" {
	run grepdumpdata "FIELD\[Market\|customfield_12326956\]:"
	check_status
}

@test "Escape Impact_customfield_12326957" {
	run grepdumpdata "FIELD\[Escape\ Impact\|customfield_12326957\]:"
	check_status
}

@test "Portfolio Solutions_customfield_12326954" {
	run grepdumpdata "FIELD\[Portfolio\ Solutions\|customfield_12326954\]:"
	check_status
}

@test "Corrective Measures_customfield_12326955" {
	run grepdumpdata "FIELD\[Corrective\ Measures\|customfield_12326955\]:"
	check_status
}

@test "Ready-Ready_customfield_12315943" {
	run grepdumpdata "FIELD\[Ready\-Ready\|customfield_12315943\]:"
	check_status
}

@test "Forum Reference_customfield_12310010" {
	run grepdumpdata "FIELD\[Forum\ Reference\|customfield_12310010\]:"
	check_status
}

@test "Planned End_customfield_12315944" {
	run grepdumpdata "FIELD\[Planned\ End\|customfield_12315944\]:"
	check_status
}

@test "QA Contact_customfield_12315948" {
	run grepdumpdata "FIELD\[QA\ Contact\|customfield_12315948\]:"
	check_status
}

@test "Product_customfield_12315949" {
	run grepdumpdata "FIELD\[Product\|customfield_12315949\]:"
	check_status
}

@test "Votes_votes" {
	run grepdumpdata "FIELD\[Votes\|votes\]:"
	check_status
}

@test "Log Work_worklog" {
	run grepdumpdata "FIELD\[Log\ Work\|worklog\]:"
	check_status
}

@test "Acceptance Criteria_customfield_12315940" {
	run grepdumpdata "FIELD\[Acceptance\ Criteria\|customfield_12315940\]:"
	check_status
}

@test "Backlogs_customfield_12315941" {
	run grepdumpdata "FIELD\[Backlogs\|customfield_12315941\]:"
	check_status
}

@test "Escape Impact_customfield_12324344" {
	run grepdumpdata "FIELD\[Escape\ Impact\|customfield_12324344\]:"
	check_status
}

@test "Penetration Testing Maturity Level_customfield_12326644" {
	run grepdumpdata "FIELD\[Penetration\ Testing\ Maturity\ Level\|customfield_12326644\]:"
	check_status
}

@test "Issue Type_issuetype" {
	run grepdumpdata "FIELD\[Issue\ Type\|issuetype\]:"
	check_status
}

@test "SDLC stage when should've been found_customfield_12324343" {
	run grepdumpdata "FIELD\[SDLC\ stage\ when\ should've\ been\ found\|customfield_12324343\]:"
	check_status
}

@test "SOA Maturity Level_customfield_12326645" {
	run grepdumpdata "FIELD\[SOA\ Maturity\ Level\|customfield_12326645\]:"
	check_status
}

@test "Threat Model Maturity Level_customfield_12326642" {
	run grepdumpdata "FIELD\[Threat\ Model\ Maturity\ Level\|customfield_12326642\]:"
	check_status
}

@test "Corrective Measures_customfield_12324345" {
	run grepdumpdata "FIELD\[Corrective\ Measures\|customfield_12324345\]:"
	check_status
}

@test "Security Architecture Review Maturity Level_customfield_12326643" {
	run grepdumpdata "FIELD\[Security\ Architecture\ Review\ Maturity\ Level\|customfield_12326643\]:"
	check_status
}

@test "Escape Reason_customfield_12324340" {
	run grepdumpdata "FIELD\[Escape\ Reason\|customfield_12324340\]:"
	check_status
}

@test "Internal Whiteboard_customfield_12322040" {
	run grepdumpdata "FIELD\[Internal\ Whiteboard\|customfield_12322040\]:"
	check_status
}

@test "SAST Maturity Level_customfield_12326640" {
	run grepdumpdata "FIELD\[SAST\ Maturity\ Level\|customfield_12326640\]:"
	check_status
}

@test "DAST Maturity Level_customfield_12326641" {
	run grepdumpdata "FIELD\[DAST\ Maturity\ Level\|customfield_12326641\]:"
	check_status
}

@test "SDLC stage when introduced_customfield_12324342" {
	run grepdumpdata "FIELD\[SDLC\ stage\ when\ introduced\|customfield_12324342\]:"
	check_status
}

@test "SDLC stage when found_customfield_12324341" {
	run grepdumpdata "FIELD\[SDLC\ stage\ when\ found\|customfield_12324341\]:"
	check_status
}

@test "Engineering Response_customfield_12310181" {
	run grepdumpdata "FIELD\[Engineering\ Response\|customfield_12310181\]:"
	check_status
}

@test "Patch Visibility_customfield_12310060" {
	run grepdumpdata "FIELD\[Patch\ Visibility\|customfield_12310060\]:"
	check_status
}

@test "Background and Context_customfield_12310180" {
	run grepdumpdata "FIELD\[Background\ and\ Context\|customfield_12310180\]:"
	check_status
}

@test "Secure Distribution Maturity Level_customfield_12326646" {
	run grepdumpdata "FIELD\[Secure\ Distribution\ Maturity\ Level\|customfield_12326646\]:"
	check_status
}

@test "Secure Signing Maturity Level_customfield_12326647" {
	run grepdumpdata "FIELD\[Secure\ Signing\ Maturity\ Level\|customfield_12326647\]:"
	check_status
}

@test "5-Acks Check_customfield_12316845" {
	run grepdumpdata "FIELD\[5\-Acks\ Check\|customfield_12316845\]:"
	check_status
}

@test "GitHub Issue_customfield_12316846" {
	run grepdumpdata "FIELD\[GitHub\ Issue\|customfield_12316846\]:"
	check_status
}

@test "Developer Comment_customfield_12316847" {
	run grepdumpdata "FIELD\[Developer\ Comment\|customfield_12316847\]:"
	check_status
}

@test "ODC Planning_customfield_12316848" {
	run grepdumpdata "FIELD\[ODC\ Planning\|customfield_12316848\]:"
	check_status
}

@test "ODC Planning Ack_customfield_12316849" {
	run grepdumpdata "FIELD\[ODC\ Planning\ Ack\|customfield_12316849\]:"
	check_status
}

@test "Steps to Reproduce_customfield_12310183" {
	run grepdumpdata "FIELD\[Steps\ to\ Reproduce\|customfield_12310183\]:"
	check_status
}

@test "Product Management Response_customfield_12310182" {
	run grepdumpdata "FIELD\[Product\ Management\ Response\|customfield_12310182\]:"
	check_status
}

@test "QE Status_customfield_12312240" {
	run grepdumpdata "FIELD\[QE\ Status\|customfield_12312240\]:"
	check_status
}

@test "Bugzilla Bug_customfield_12316840" {
	run grepdumpdata "FIELD\[Bugzilla\ Bug\|customfield_12316840\]:"
	check_status
}

@test "Sync Failure Flag_customfield_12316841" {
	run grepdumpdata "FIELD\[Sync\ Failure\ Flag\|customfield_12316841\]:"
	check_status
}

@test "Sync Failure Message_customfield_12316842" {
	run grepdumpdata "FIELD\[Sync\ Failure\ Message\|customfield_12316842\]:"
	check_status
}

@test "Whiteboard_customfield_12316843" {
	run grepdumpdata "FIELD\[Whiteboard\|customfield_12316843\]:"
	check_status
}

@test "Time to resolution_customfield_12325441" {
	run grepdumpdata "FIELD\[Time\ to\ resolution\|customfield_12325441\]:"
	check_status
}

@test "Time to first response_customfield_12325442" {
	run grepdumpdata "FIELD\[Time\ to\ first\ response\|customfield_12325442\]:"
	check_status
}

@test "Approvers_customfield_12325440" {
	run grepdumpdata "FIELD\[Approvers\|customfield_12325440\]:"
	check_status
}

@test "Patch Repository Link_customfield_12310071" {
	run grepdumpdata "FIELD\[Patch\ Repository\ Link\|customfield_12310071\]:"
	check_status
}

@test "Patch Instructions_customfield_12310070" {
	run grepdumpdata "FIELD\[Patch\ Instructions\|customfield_12310070\]:"
	check_status
}

@test "Doc Required_customfield_12315640" {
	run grepdumpdata "FIELD\[Doc\ Required\|customfield_12315640\]:"
	check_status
}

@test "Stackoverflow ID_customfield_12313340" {
	run grepdumpdata "FIELD\[Stackoverflow\ ID\|customfield_12313340\]:"
	check_status
}

@test "Service Delivery Planning ACK_customfield_12316850" {
	run grepdumpdata "FIELD\[Service\ Delivery\ Planning\ ACK\|customfield_12316850\]:"
	check_status
}

@test "Funding State_customfield_12317940" {
	run grepdumpdata "FIELD\[Funding\ State\|customfield_12317940\]:"
	check_status
}

@test "Funding Strategy_customfield_12317941" {
	run grepdumpdata "FIELD\[Funding\ Strategy\|customfield_12317941\]:"
	check_status
}

@test "Jira Link_customfield_12324443" {
	run grepdumpdata "FIELD\[Jira\ Link\|customfield_12324443\]:"
	check_status
}

@test "PX Impact Range_customfield_12322143" {
	run grepdumpdata "FIELD\[PX\ Impact\ Range\|customfield_12322143\]:"
	check_status
}

@test "Other Savings_customfield_12324442" {
	run grepdumpdata "FIELD\[Other\ Savings\|customfield_12324442\]:"
	check_status
}

@test "Risk Identified Date_customfield_12322144" {
	run grepdumpdata "FIELD\[Risk\ Identified\ Date\|customfield_12322144\]:"
	check_status
}

@test "Additional Approvers_customfield_12322145" {
	run grepdumpdata "FIELD\[Additional\ Approvers\|customfield_12322145\]:"
	check_status
}

@test "Security Approvals_customfield_12322146" {
	run grepdumpdata "FIELD\[Security\ Approvals\|customfield_12322146\]:"
	check_status
}

@test "PX Review Complete_customfield_12322140" {
	run grepdumpdata "FIELD\[PX\ Review\ Complete\|customfield_12322140\]:"
	check_status
}

@test "SLA Date_customfield_12326740" {
	run grepdumpdata "FIELD\[SLA\ Date\|customfield_12326740\]:"
	check_status
}

@test "Annual Cost Savings/Avoidance_customfield_12324441" {
	run grepdumpdata "FIELD\[Annual\ Cost\ Savings/Avoidance\|customfield_12324441\]:"
	check_status
}

@test "PX Technical Impact_customfield_12322141" {
	run grepdumpdata "FIELD\[PX\ Technical\ Impact\|customfield_12322141\]:"
	check_status
}

@test "Annual Time Savings_customfield_12324440" {
	run grepdumpdata "FIELD\[Annual\ Time\ Savings\|customfield_12324440\]:"
	check_status
}

@test "PX Priority Data_customfield_12322142" {
	run grepdumpdata "FIELD\[PX\ Priority\ Data\|customfield_12322142\]:"
	check_status
}

@test "Dev Target end_customfield_12322148" {
	run grepdumpdata "FIELD\[Dev\ Target\ end\|customfield_12322148\]:"
	check_status
}

@test "Time Tracking_timetracking" {
	run grepdumpdata "FIELD\[Time\ Tracking\|timetracking\]:"
	check_status
}

@test "GSS Priority_customfield_12312340" {
	run grepdumpdata "FIELD\[GSS\ Priority\|customfield_12312340\]:"
	check_status
}

@test "Upstream Jira_customfield_12314640" {
	run grepdumpdata "FIELD\[Upstream\ Jira\|customfield_12314640\]:"
	check_status
}

@test "Customer Name_customfield_12310160" {
	run grepdumpdata "FIELD\[Customer\ Name\|customfield_12310160\]:"
	check_status
}

@test "Team Confidence_customfield_12316940" {
	run grepdumpdata "FIELD\[Team\ Confidence\|customfield_12316940\]:"
	check_status
}

@test "QE Confidence_customfield_12316941" {
	run grepdumpdata "FIELD\[QE\ Confidence\|customfield_12316941\]:"
	check_status
}

@test "Doc Confidence_customfield_12316942" {
	run grepdumpdata "FIELD\[Doc\ Confidence\|customfield_12316942\]:"
	check_status
}

@test "Business Value_customfield_12316943" {
	run grepdumpdata "FIELD\[Business\ Value\|customfield_12316943\]:"
	check_status
}

@test "Anomaly_customfield_12323240" {
	run grepdumpdata "FIELD\[Anomaly\|customfield_12323240\]:"
	check_status
}

@test "Exception Count_customfield_12322150" {
	run grepdumpdata "FIELD\[Exception\ Count\|customfield_12322150\]:"
	check_status
}

@test "Product/Service_customfield_12325540" {
	run grepdumpdata "FIELD\[Product/Service\|customfield_12325540\]:"
	check_status
}

@test "Security Controls_customfield_12322151" {
	run grepdumpdata "FIELD\[Security\ Controls\|customfield_12322151\]:"
	check_status
}

@test "Blocked by Bugzilla Bug_customfield_12322152" {
	run grepdumpdata "FIELD\[Blocked\ by\ Bugzilla\ Bug\|customfield_12322152\]:"
	check_status
}

@test "Request Clones_customfield_12323242" {
	run grepdumpdata "FIELD\[Request\ Clones\|customfield_12323242\]:"
	check_status
}

@test "Anomaly Criticality_customfield_12323241" {
	run grepdumpdata "FIELD\[Anomaly\ Criticality\|customfield_12323241\]:"
	check_status
}

@test "Affects Testing_customfield_12310170" {
	run grepdumpdata "FIELD\[Affects\ Testing\|customfield_12310170\]:"
	check_status
}

@test "Environment_environment" {
	run grepdumpdata "FIELD\[Environment\|environment\]:"
	check_status
}

@test "Affected Jars_customfield_12313443" {
	run grepdumpdata "FIELD\[Affected\ Jars\|customfield_12313443\]:"
	check_status
}

@test "Epic Colour_customfield_12311143" {
	run grepdumpdata "FIELD\[Epic\ Colour\|customfield_12311143\]:"
	check_status
}

@test "PDD Priority_customfield_12313442" {
	run grepdumpdata "FIELD\[PDD\ Priority\|customfield_12313442\]:"
	check_status
}

@test "Epic Name_customfield_12311141" {
	run grepdumpdata "FIELD\[Epic\ Name\|customfield_12311141\]:"
	check_status
}

@test "SFDC Cases Links_customfield_12313441" {
	run grepdumpdata "FIELD\[SFDC\ Cases\ Links\|customfield_12313441\]:"
	check_status
}

@test "issueFunction_customfield_12315740" {
	run grepdumpdata "FIELD\[issueFunction\|customfield_12315740\]:"
	check_status
}

@test "Epic Status_customfield_12311142" {
	run grepdumpdata "FIELD\[Epic\ Status\|customfield_12311142\]:"
	check_status
}

@test "SFDC Cases Counter_customfield_12313440" {
	run grepdumpdata "FIELD\[SFDC\ Cases\ Counter\|customfield_12313440\]:"
	check_status
}

@test "Due Date_duedate" {
	run grepdumpdata "FIELD\[Due\ Date\|duedate\]:"
	check_status
}

@test "Component Fix Version(s)_customfield_12310173" {
	run grepdumpdata "FIELD\[Component\ Fix\ Version\(s\)\|customfield_12310173\]:"
	check_status
}

@test "Epic Link_customfield_12311140" {
	run grepdumpdata "FIELD\[Epic\ Link\|customfield_12311140\]:"
	check_status
}

@test "EBS Account Number_customfield_12326440" {
	run grepdumpdata "FIELD\[EBS\ Account\ Number\|customfield_12326440\]:"
	check_status
}

@test "MDM Account Reference_customfield_12326441" {
	run grepdumpdata "FIELD\[MDM\ Account\ Reference\|customfield_12326441\]:"
	check_status
}

@test "cee_cir_customfield_12314340" {
	run grepdumpdata "FIELD\[cee_cir\|customfield_12314340\]:"
	check_status
}

@test "Work Category_customfield_12324140" {
	run grepdumpdata "FIELD\[Work\ Category\|customfield_12324140\]:"
	check_status
}

@test "Request participants_customfield_12325242" {
	run grepdumpdata "FIELD\[Request\ participants\|customfield_12325242\]:"
	check_status
}

@test "Approvals_customfield_12325241" {
	run grepdumpdata "FIELD\[Approvals\|customfield_12325241\]:"
	check_status
}

@test "Satisfaction_customfield_12325243" {
	run grepdumpdata "FIELD\[Satisfaction\|customfield_12325243\]:"
	check_status
}

@test "Parent Link_customfield_12313140" {
	run grepdumpdata "FIELD\[Parent\ Link\|customfield_12313140\]:"
	check_status
}

@test "QE Estimate_customfield_12313145" {
	run grepdumpdata "FIELD\[QE\ Estimate\|customfield_12313145\]:"
	check_status
}

@test "Remaining Estimate_timeestimate" {
	run grepdumpdata "FIELD\[Remaining\ Estimate\|timeestimate\]:"
	check_status
}

@test "EAP PT Community Docs (CD)_customfield_12313143" {
	run grepdumpdata "FIELD\[EAP\ PT\ Community\ Docs\ \(CD\)\|customfield_12313143\]:"
	check_status
}

@test "EAP PT Test Dev (TD)_customfield_12313144" {
	run grepdumpdata "FIELD\[EAP\ PT\ Test\ Dev\ \(TD\)\|customfield_12313144\]:"
	check_status
}

@test "Planning Status_customfield_12317740" {
	run grepdumpdata "FIELD\[Planning\ Status\|customfield_12317740\]:"
	check_status
}

@test "Linked major incidents_customfield_12325240" {
	run grepdumpdata "FIELD\[Linked\ major\ incidents\|customfield_12325240\]:"
	check_status
}

@test "Status_status" {
	run grepdumpdata "FIELD\[Status\|status\]:"
	check_status
}

@test "SRE Contact_customfield_12324240" {
	run grepdumpdata "FIELD\[SRE\ Contact\|customfield_12324240\]:"
	check_status
}

@test "AssignedTeam_customfield_12326540" {
	run grepdumpdata "FIELD\[AssignedTeam\|customfield_12326540\]:"
	check_status
}

@test "Tester_customfield_12310080" {
	run grepdumpdata "FIELD\[Tester\|customfield_12310080\]:"
	check_status
}

@test "Archived_archiveddate" {
	run grepdumpdata "FIELD\[Archived\|archiveddate\]:"
	check_status
}

@test "Account Number_customfield_12316747" {
	run grepdumpdata "FIELD\[Account\ Number\|customfield_12316747\]:"
	check_status
}

@test "Architect_customfield_12316749" {
	run grepdumpdata "FIELD\[Architect\|customfield_12316749\]:"
	check_status
}

@test "Σ Remaining Estimate_aggregatetimeestimate" {
	run grepdumpdata "FIELD\[Σ\ Remaining\ Estimate\|aggregatetimeestimate\]:"
	check_status
}

@test "Class of work_customfield_12312142" {
	run grepdumpdata "FIELD\[Class\ of\ work\|customfield_12312142\]:"
	check_status
}

@test "Prod build version_customfield_12316740" {
	run grepdumpdata "FIELD\[Prod\ build\ version\|customfield_12316740\]:"
	check_status
}

@test "QE ACK_customfield_12316745" {
	run grepdumpdata "FIELD\[QE\ ACK\|customfield_12316745\]:"
	check_status
}

@test "Creator_creator" {
	run grepdumpdata "FIELD\[Creator\|creator\]:"
	check_status
}

@test "Satisfaction date_customfield_12325342" {
	run grepdumpdata "FIELD\[Satisfaction\ date\|customfield_12325342\]:"
	check_status
}

@test "Groups_customfield_12325343" {
	run grepdumpdata "FIELD\[Groups\|customfield_12325343\]:"
	check_status
}

@test "Customer Request Type_customfield_12325340" {
	run grepdumpdata "FIELD\[Customer\ Request\ Type\|customfield_12325340\]:"
	check_status
}

@test "Organizations_customfield_12325341" {
	run grepdumpdata "FIELD\[Organizations\|customfield_12325341\]:"
	check_status
}

@test "Workaround Description_customfield_12310091" {
	run grepdumpdata "FIELD\[Workaround\ Description\|customfield_12310091\]:"
	check_status
}

@test "Workaround_customfield_12310090" {
	run grepdumpdata "FIELD\[Workaround\|customfield_12310090\]:"
	check_status
}

@test "Estimated Difficulty_customfield_12310092" {
	run grepdumpdata "FIELD\[Estimated\ Difficulty\|customfield_12310092\]:"
	check_status
}

@test "Flagged_customfield_12315542" {
	run grepdumpdata "FIELD\[Flagged\|customfield_12315542\]:"
	check_status
}

@test "Regression Test_customfield_12315541" {
	run grepdumpdata "FIELD\[Regression\ Test\|customfield_12315541\]:"
	check_status
}

@test "EAP Docs SME_customfield_12315540" {
	run grepdumpdata "FIELD\[EAP\ Docs\ SME\|customfield_12315540\]:"
	check_status
}

@test "Team_customfield_12313240" {
	run grepdumpdata "FIELD\[Team\|customfield_12313240\]:"
	check_status
}

@test "Technical Lead_customfield_12316750" {
	run grepdumpdata "FIELD\[Technical\ Lead\|customfield_12316750\]:"
	check_status
}

@test "Designer_customfield_12316751" {
	run grepdumpdata "FIELD\[Designer\|customfield_12316751\]:"
	check_status
}

@test "PX Scheduling Request_customfield_12323040" {
	run grepdumpdata "FIELD\[PX\ Scheduling\ Request\|customfield_12323040\]:"
	check_status
}

@test "Product Manager_customfield_12316752" {
	run grepdumpdata "FIELD\[Product\ Manager\|customfield_12316752\]:"
	check_status
}

@test "Manager_customfield_12316753" {
	run grepdumpdata "FIELD\[Manager\|customfield_12316753\]:"
	check_status
}

@test "BZ Partner_customfield_12317843" {
	run grepdumpdata "FIELD\[BZ\ Partner\|customfield_12317843\]:"
	check_status
}

@test "Time Spent_timespent" {
	run grepdumpdata "FIELD\[Time\ Spent\|timespent\]:"
	check_status
}

@test "RICE Score_customfield_12326242" {
	run grepdumpdata "FIELD\[RICE\ Score\|customfield_12326242\]:"
	check_status
}

@test "Test Coverage_customfield_12320940" {
	run grepdumpdata "FIELD\[Test\ Coverage\|customfield_12320940\]:"
	check_status
}

@test "Σ Time Spent_aggregatetimespent" {
	run grepdumpdata "FIELD\[Σ\ Time\ Spent\|aggregatetimespent\]:"
	check_status
}

@test "Pervasiveness_customfield_12320943" {
	run grepdumpdata "FIELD\[Pervasiveness\|customfield_12320943\]:"
	check_status
}

@test "Willingness to Pay_customfield_12320941" {
	run grepdumpdata "FIELD\[Willingness\ to\ Pay\|customfield_12320941\]:"
	check_status
}

@test "Cost of Delay_customfield_12326240" {
	run grepdumpdata "FIELD\[Cost\ of\ Delay\|customfield_12326240\]:"
	check_status
}

@test "Work Source_customfield_12316441" {
	run grepdumpdata "FIELD\[Work\ Source\|customfield_12316441\]:"
	check_status
}

@test "Work Ratio_workratio" {
	run grepdumpdata "FIELD\[Work\ Ratio\|workratio\]:"
	check_status
}

@test "Customer Cloud Subscription (CCS)_customfield_12316442" {
	run grepdumpdata "FIELD\[Customer\ Cloud\ Subscription\ \(CCS\)\|customfield_12316442\]:"
	check_status
}

@test "Portfolio Solutions_customfield_12318740" {
	run grepdumpdata "FIELD\[Portfolio\ Solutions\|customfield_12318740\]:"
	check_status
}

@test "WSJF_customfield_12326241" {
	run grepdumpdata "FIELD\[WSJF\|customfield_12326241\]:"
	check_status
}

@test "Cluster Admin Enabled_customfield_12316443" {
	run grepdumpdata "FIELD\[Cluster\ Admin\ Enabled\|customfield_12316443\]:"
	check_status
}

@test "Cloud Platform_customfield_12316444" {
	run grepdumpdata "FIELD\[Cloud\ Platform\|customfield_12316444\]:"
	check_status
}

@test "Support Scope_customfield_12317540" {
	run grepdumpdata "FIELD\[Support\ Scope\|customfield_12317540\]:"
	check_status
}

@test "EAP Testing By_customfield_12315240" {
	run grepdumpdata "FIELD\[EAP\ Testing\ By\|customfield_12315240\]:"
	check_status
}

@test "Experience_customfield_12320948" {
	run grepdumpdata "FIELD\[Experience\|customfield_12320948\]:"
	check_status
}

@test "Original Estimate_customfield_12317307" {
	run grepdumpdata "FIELD\[Original\ Estimate\|customfield_12317307\]:"
	check_status
}

@test "Market_customfield_12320947" {
	run grepdumpdata "FIELD\[Market\|customfield_12320947\]:"
	check_status
}

@test "BZ URL_customfield_12317309" {
	run grepdumpdata "FIELD\[BZ\ URL\|customfield_12317309\]:"
	check_status
}

@test "Intelligence Requested_customfield_12320946" {
	run grepdumpdata "FIELD\[Intelligence\ Requested\|customfield_12320946\]:"
	check_status
}

@test "Risk Category_customfield_12320945" {
	run grepdumpdata "FIELD\[Risk\ Category\|customfield_12320945\]:"
	check_status
}

@test "External issue ID_customfield_12319840" {
	run grepdumpdata "FIELD\[External\ issue\ ID\|customfield_12319840\]:"
	check_status
}

@test "Risk Type_customfield_12317301" {
	run grepdumpdata "FIELD\[Risk\ Type\|customfield_12317301\]:"
	check_status
}

@test "Risk Probability_customfield_12317302" {
	run grepdumpdata "FIELD\[Risk\ Probability\|customfield_12317302\]:"
	check_status
}

@test "Risk Proximity_customfield_12317303" {
	run grepdumpdata "FIELD\[Risk\ Proximity\|customfield_12317303\]:"
	check_status
}

@test "Risk Impact Level_customfield_12317304" {
	run grepdumpdata "FIELD\[Risk\ Impact\ Level\|customfield_12317304\]:"
	check_status
}

@test "Risk impact description_customfield_12317305" {
	run grepdumpdata "FIELD\[Risk\ impact\ description\|customfield_12317305\]:"
	check_status
}

@test "Risk mitigation/contingency_customfield_12317306" {
	run grepdumpdata "FIELD\[Risk\ mitigation/contingency\|customfield_12317306\]:"
	check_status
}

@test "Operating System_Lab_customfield_12324043" {
	run grepdumpdata "FIELD\[Operating\ System_Lab\|customfield_12324043\]:"
	check_status
}

@test "Actual Effort_customfield_12316548" {
	run grepdumpdata "FIELD\[Actual\ Effort\|customfield_12316548\]:"
	check_status
}

@test "Chapter_customfield_12316549" {
	run grepdumpdata "FIELD\[Chapter\|customfield_12316549\]:"
	check_status
}

@test "EAP PT Pre-Checked (PC)_customfield_12314245" {
	run grepdumpdata "FIELD\[EAP\ PT\ Pre\-Checked\ \(PC\)\|customfield_12314245\]:"
	check_status
}

@test "EAP PT Product Docs (PD)_customfield_12314244" {
	run grepdumpdata "FIELD\[EAP\ PT\ Product\ Docs\ \(PD\)\|customfield_12314244\]:"
	check_status
}

@test "EAP PT Docs Analysis (DA)_customfield_12314243" {
	run grepdumpdata "FIELD\[EAP\ PT\ Docs\ Analysis\ \(DA\)\|customfield_12314243\]:"
	check_status
}

@test "EAP PT Test Plan (TP)_customfield_12314242" {
	run grepdumpdata "FIELD\[EAP\ PT\ Test\ Plan\ \(TP\)\|customfield_12314242\]:"
	check_status
}

@test "EAP PT Analysis Document (AD)_customfield_12314241" {
	run grepdumpdata "FIELD\[EAP\ PT\ Analysis\ Document\ \(AD\)\|customfield_12314241\]:"
	check_status
}

@test "Marketing Info_customfield_12318840" {
	run grepdumpdata "FIELD\[Marketing\ Info\|customfield_12318840\]:"
	check_status
}

@test "Reviewer_customfield_12316540" {
	run grepdumpdata "FIELD\[Reviewer\|customfield_12316540\]:"
	check_status
}

@test "T-Shirt Size_customfield_12316541" {
	run grepdumpdata "FIELD\[T\-Shirt\ Size\|customfield_12316541\]:"
	check_status
}

@test "Commit Hashes_customfield_12324041" {
	run grepdumpdata "FIELD\[Commit\ Hashes\|customfield_12324041\]:"
	check_status
}

@test "Ready_customfield_12316542" {
	run grepdumpdata "FIELD\[Ready\|customfield_12316542\]:"
	check_status
}

@test "Blocked_customfield_12316543" {
	run grepdumpdata "FIELD\[Blocked\|customfield_12316543\]:"
	check_status
}

@test "Marketing Info Ready_customfield_12318841" {
	run grepdumpdata "FIELD\[Marketing\ Info\ Ready\|customfield_12318841\]:"
	check_status
}

@test "Product Documentation Required_customfield_12324040" {
	run grepdumpdata "FIELD\[Product\ Documentation\ Required\|customfield_12324040\]:"
	check_status
}

@test "Blocked Reason_customfield_12316544" {
	run grepdumpdata "FIELD\[Blocked\ Reason\|customfield_12316544\]:"
	check_status
}

@test "Owner_customfield_12316545" {
	run grepdumpdata "FIELD\[Owner\|customfield_12316545\]:"
	check_status
}

@test "Evidence Score_customfield_12316546" {
	run grepdumpdata "FIELD\[Evidence\ Score\|customfield_12316546\]:"
	check_status
}

@test "Discussed with Team_customfield_12316547" {
	run grepdumpdata "FIELD\[Discussed\ with\ Team\|customfield_12316547\]:"
	check_status
}

@test "Test Plan_customfield_12313040" {
	run grepdumpdata "FIELD\[Test\ Plan\|customfield_12313040\]:"
	check_status
}

@test "Analysis Document_customfield_12313041" {
	run grepdumpdata "FIELD\[Analysis\ Document\|customfield_12313041\]:"
	check_status
}

@test "Microrelease version_customfield_12313042" {
	run grepdumpdata "FIELD\[Microrelease\ version\|customfield_12313042\]:"
	check_status
}

@test "DevTestDoc_customfield_12317640" {
	run grepdumpdata "FIELD\[DevTestDoc\|customfield_12317640\]:"
	check_status
}

@test "Target Version_customfield_12319940" {
	run grepdumpdata "FIELD\[Target\ Version\|customfield_12319940\]:"
	check_status
}

@test "Functional Safety Justification_customfield_12325141" {
	run grepdumpdata "FIELD\[Functional\ Safety\ Justification\|customfield_12325141\]:"
	check_status
}

@test "EXD-Service_customfield_12317401" {
	run grepdumpdata "FIELD\[EXD\-Service\|customfield_12317401\]:"
	check_status
}

@test "Functional Safety Triage_customfield_12325140" {
	run grepdumpdata "FIELD\[Functional\ Safety\ Triage\|customfield_12325140\]:"
	check_status
}

@test "EXD-WorkType_customfield_12317403" {
	run grepdumpdata "FIELD\[EXD\-WorkType\|customfield_12317403\]:"
	check_status
}

@test "Commitment_customfield_12317404" {
	run grepdumpdata "FIELD\[Commitment\|customfield_12317404\]:"
	check_status
}

@test "Requesting Teams_customfield_12317405" {
	run grepdumpdata "FIELD\[Requesting\ Teams\|customfield_12317405\]:"
	check_status
}

@test "Planning_customfield_12316240" {
	run grepdumpdata "FIELD\[Planning\|customfield_12316240\]:"
	check_status
}

@test "BZ needinfo_customfield_12317330" {
	run grepdumpdata "FIELD\[BZ\ needinfo\|customfield_12317330\]:"
	check_status
}

@test "Design Doc_customfield_12316241" {
	run grepdumpdata "FIELD\[Design\ Doc\|customfield_12316241\]:"
	check_status
}

@test "Risk Score_customfield_12319751" {
	run grepdumpdata "FIELD\[Risk\ Score\|customfield_12319751\]:"
	check_status
}

@test "BZ rhel-8.0.z_customfield_12317331" {
	run grepdumpdata "FIELD\[BZ\ rhel\-8\.0\.z\|customfield_12317331\]:"
	check_status
}

@test "Message For OHSS Project_customfield_12318540" {
	run grepdumpdata "FIELD\[Message\ For\ OHSS\ Project\|customfield_12318540\]:"
	check_status
}

@test "QEStatus_customfield_12316242" {
	run grepdumpdata "FIELD\[QEStatus\|customfield_12316242\]:"
	check_status
}

@test "Urgency_customfield_12320741" {
	run grepdumpdata "FIELD\[Urgency\|customfield_12320741\]:"
	check_status
}

@test "Impact_customfield_12320740" {
	run grepdumpdata "FIELD\[Impact\|customfield_12320740\]:"
	check_status
}

@test "ZStream Target Release_customfield_12317332" {
	run grepdumpdata "FIELD\[ZStream\ Target\ Release\|customfield_12317332\]:"
	check_status
}

@test "BZ blocker_customfield_12317333" {
	run grepdumpdata "FIELD\[BZ\ blocker\|customfield_12317333\]:"
	check_status
}

@test "Needs Product Docs_customfield_12316245" {
	run grepdumpdata "FIELD\[Needs\ Product\ Docs\|customfield_12316245\]:"
	check_status
}

@test "zstream_customfield_12317334" {
	run grepdumpdata "FIELD\[zstream\|customfield_12317334\]:"
	check_status
}

@test "BZ Version_customfield_12317335" {
	run grepdumpdata "FIELD\[BZ\ Version\|customfield_12317335\]:"
	check_status
}

@test "BZ Docs Contact_customfield_12317336" {
	run grepdumpdata "FIELD\[BZ\ Docs\ Contact\|customfield_12317336\]:"
	check_status
}

@test "BZ requires_doc_text_customfield_12317337" {
	run grepdumpdata "FIELD\[BZ\ requires_doc_text\|customfield_12317337\]:"
	check_status
}

@test "Doc Commitment_customfield_12317338" {
	run grepdumpdata "FIELD\[Doc\ Commitment\|customfield_12317338\]:"
	check_status
}

@test "Sprint_customfield_12310940" {
	run grepdumpdata "FIELD\[Sprint\|customfield_12310940\]:"
	check_status
}

@test "Link to documentation_customfield_12316250" {
	run grepdumpdata "FIELD\[Link\ to\ documentation\|customfield_12316250\]:"
	check_status
}

@test "OS_customfield_12317340" {
	run grepdumpdata "FIELD\[OS\|customfield_12317340\]:"
	check_status
}

@test "Public Target Launch Date_customfield_12317341" {
	run grepdumpdata "FIELD\[Public\ Target\ Launch\ Date\|customfield_12317341\]:"
	check_status
}

@test "Contributing Groups_customfield_12319640" {
	run grepdumpdata "FIELD\[Contributing\ Groups\|customfield_12319640\]:"
	check_status
}

@test "3scale PT Verified Product_customfield_12315043" {
	run grepdumpdata "FIELD\[3scale\ PT\ Verified\ Product\|customfield_12315043\]:"
	check_status
}

@test "3scale PT Released In Saas_customfield_12315042" {
	run grepdumpdata "FIELD\[3scale\ PT\ Released\ In\ Saas\|customfield_12315042\]:"
	check_status
}

@test "3scale PT Docs_customfield_12315041" {
	run grepdumpdata "FIELD\[3scale\ PT\ Docs\|customfield_12315041\]:"
	check_status
}

@test "3scale PT Product Specs_customfield_12315040" {
	run grepdumpdata "FIELD\[3scale\ PT\ Product\ Specs\|customfield_12315040\]:"
	check_status
}

@test "Supply Chain STI_customfield_12321840" {
	run grepdumpdata "FIELD\[Supply\ Chain\ STI\|customfield_12321840\]:"
	check_status
}

@test "Labels_labels" {
	run grepdumpdata "FIELD\[Labels\|labels\]:"
	check_status
}

@test "3scale PT Product Update Ready_customfield_12315044" {
	run grepdumpdata "FIELD\[3scale\ PT\ Product\ Update\ Ready\|customfield_12315044\]:"
	check_status
}

@test "Target Upstream Version_customfield_12317343" {
	run grepdumpdata "FIELD\[Target\ Upstream\ Version\|customfield_12317343\]:"
	check_status
}

@test "Close Duplicate Candidate_customfield_12317344" {
	run grepdumpdata "FIELD\[Close\ Duplicate\ Candidate\|customfield_12317344\]:"
	check_status
}

@test "Partner Requirement State_customfield_12317345" {
	run grepdumpdata "FIELD\[Partner\ Requirement\ State\|customfield_12317345\]:"
	check_status
}

@test "BZ Target Release_customfield_12317346" {
	run grepdumpdata "FIELD\[BZ\ Target\ Release\|customfield_12317346\]:"
	check_status
}

@test "Upstream Kernel Target_customfield_12317347" {
	run grepdumpdata "FIELD\[Upstream\ Kernel\ Target\|customfield_12317347\]:"
	check_status
}

@test "EPM priority_customfield_12317348" {
	run grepdumpdata "FIELD\[EPM\ priority\|customfield_12317348\]:"
	check_status
}

@test "Case Link_customfield_12317349" {
	run grepdumpdata "FIELD\[Case\ Link\|customfield_12317349\]:"
	check_status
}

@test "Component/s_components" {
	run grepdumpdata "FIELD\[Component/s\|components\]:"
	check_status
}

@test "BZ Flags_customfield_12318640" {
	run grepdumpdata "FIELD\[BZ\ Flags\|customfield_12318640\]:"
	check_status
}

@test "Service / (sub)product_customfield_12316340" {
	run grepdumpdata "FIELD\[Service\ /\ \(sub\)product\|customfield_12316340\]:"
	check_status
}

@test "Department_customfield_12316341" {
	run grepdumpdata "FIELD\[Department\|customfield_12316341\]:"
	check_status
}

@test "Status Summary_customfield_12320841" {
	run grepdumpdata "FIELD\[Status\ Summary\|customfield_12320841\]:"
	check_status
}

@test "Release Type_customfield_12320840" {
	run grepdumpdata "FIELD\[Release\ Type\|customfield_12320840\]:"
	check_status
}

@test "Original story points_customfield_12314040" {
	run grepdumpdata "FIELD\[Original\ story\ points\|customfield_12314040\]:"
	check_status
}

@test "Color Status_customfield_12320845" {
	run grepdumpdata "FIELD\[Color\ Status\|customfield_12320845\]:"
	check_status
}

@test "Customer Impact_customfield_12320844" {
	run grepdumpdata "FIELD\[Customer\ Impact\|customfield_12320844\]:"
	check_status
}

@test "UX or UI Contact_customfield_12320843" {
	run grepdumpdata "FIELD\[UX\ or\ UI\ Contact\|customfield_12320843\]:"
	check_status
}

@test "Documentation Type_customfield_12320842" {
	run grepdumpdata "FIELD\[Documentation\ Type\|customfield_12320842\]:"
	check_status
}

@test "BZ Keywords_customfield_12317318" {
	run grepdumpdata "FIELD\[BZ\ Keywords\|customfield_12317318\]:"
	check_status
}

@test "BZ exception_customfield_12317319" {
	run grepdumpdata "FIELD\[BZ\ exception\|customfield_12317319\]:"
	check_status
}

@test "Additional Assignees_customfield_12316342" {
	run grepdumpdata "FIELD\[Additional\ Assignees\|customfield_12316342\]:"
	check_status
}

@test "BZ Doc Type_customfield_12317310" {
	run grepdumpdata "FIELD\[BZ\ Doc\ Type\|customfield_12317310\]:"
	check_status
}

@test "BZ QA Whiteboard_customfield_12317311" {
	run grepdumpdata "FIELD\[BZ\ QA\ Whiteboard\|customfield_12317311\]:"
	check_status
}

@test "OpenShift Planning Ack_customfield_12316343" {
	run grepdumpdata "FIELD\[OpenShift\ Planning\ Ack\|customfield_12316343\]:"
	check_status
}

@test "BZ Internal Whiteboard_customfield_12317312" {
	run grepdumpdata "FIELD\[BZ\ Internal\ Whiteboard\|customfield_12317312\]:"
	check_status
}

@test "Exception Type_customfield_12326140" {
	run grepdumpdata "FIELD\[Exception\ Type\|customfield_12326140\]:"
	check_status
}

@test "Release Note Text_customfield_12317313" {
	run grepdumpdata "FIELD\[Release\ Note\ Text\|customfield_12317313\]:"
	check_status
}

@test "Quarter_customfield_12317314" {
	run grepdumpdata "FIELD\[Quarter\|customfield_12317314\]:"
	check_status
}

@test "release_customfield_12317315" {
	run grepdumpdata "FIELD\[release\|customfield_12317315\]:"
	check_status
}

@test "Architecture_customfield_12316348" {
	run grepdumpdata "FIELD\[Architecture\|customfield_12316348\]:"
	check_status
}

@test "BZ Target Milestone_customfield_12317317" {
	run grepdumpdata "FIELD\[BZ\ Target\ Milestone\|customfield_12317317\]:"
	check_status
}

@test "Cluster ID_customfield_12316349" {
	run grepdumpdata "FIELD\[Cluster\ ID\|customfield_12316349\]:"
	check_status
}

@test "Aha! URL_customfield_12317440" {
	run grepdumpdata "FIELD\[Aha!\ URL\|customfield_12317440\]:"
	check_status
}

@test "Approved_customfield_12319740" {
	run grepdumpdata "FIELD\[Approved\|customfield_12319740\]:"
	check_status
}

@test "Current Status_customfield_12317320" {
	run grepdumpdata "FIELD\[Current\ Status\|customfield_12317320\]:"
	check_status
}

@test "Satellite Team_customfield_12317441" {
	run grepdumpdata "FIELD\[Satellite\ Team\|customfield_12317441\]:"
	check_status
}

@test "Size_customfield_12320852" {
	run grepdumpdata "FIELD\[Size\|customfield_12320852\]:"
	check_status
}

@test "Developer_customfield_12315141" {
	run grepdumpdata "FIELD\[Developer\|customfield_12315141\]:"
	check_status
}

@test "Sub-System Group_customfield_12320851" {
	run grepdumpdata "FIELD\[Sub\-System\ Group\|customfield_12320851\]:"
	check_status
}

@test "Reporter_reporter" {
	run grepdumpdata "FIELD\[Reporter\|reporter\]:"
	check_status
}

@test "3Scale PT Tested upstream_customfield_12315140" {
	run grepdumpdata "FIELD\[3Scale\ PT\ Tested\ upstream\|customfield_12315140\]:"
	check_status
}

@test "Release Note Type_customfield_12320850" {
	run grepdumpdata "FIELD\[Release\ Note\ Type\|customfield_12320850\]:"
	check_status
}

@test "Supply Chain Program_customfield_12321940" {
	run grepdumpdata "FIELD\[Supply\ Chain\ Program\|customfield_12321940\]:"
	check_status
}

@test "PM Score_customfield_12317329" {
	run grepdumpdata "FIELD\[PM\ Score\|customfield_12317329\]:"
	check_status
}

@test "Effort_customfield_12320848" {
	run grepdumpdata "FIELD\[Effort\|customfield_12320848\]:"
	check_status
}

@test "Confidence_customfield_12320847" {
	run grepdumpdata "FIELD\[Confidence\|customfield_12320847\]:"
	check_status
}

@test "Reach_customfield_12320846" {
	run grepdumpdata "FIELD\[Reach\|customfield_12320846\]:"
	check_status
}

@test "BZ Assignee_customfield_12317321" {
	run grepdumpdata "FIELD\[BZ\ Assignee\|customfield_12317321\]:"
	check_status
}

@test "Release Commit Exception_customfield_12319742" {
	run grepdumpdata "FIELD\[Release\ Commit\ Exception\|customfield_12319742\]:"
	check_status
}

@test "Upstream Discussion_customfield_12317442" {
	run grepdumpdata "FIELD\[Upstream\ Discussion\|customfield_12317442\]:"
	check_status
}

@test "Progress_progress" {
	run grepdumpdata "FIELD\[Progress\|progress\]:"
	check_status
}

@test "BZ Doc Text_customfield_12317322" {
	run grepdumpdata "FIELD\[BZ\ Doc\ Text\|customfield_12317322\]:"
	check_status
}

@test "Market Intelligence Score_customfield_12319741" {
	run grepdumpdata "FIELD\[Market\ Intelligence\ Score\|customfield_12319741\]:"
	check_status
}

@test "Responsible_customfield_12319744" {
	run grepdumpdata "FIELD\[Responsible\|customfield_12319744\]:"
	check_status
}

@test "BZ Product_customfield_12317324" {
	run grepdumpdata "FIELD\[BZ\ Product\|customfield_12317324\]:"
	check_status
}

@test "Release Blocker_customfield_12319743" {
	run grepdumpdata "FIELD\[Release\ Blocker\|customfield_12319743\]:"
	check_status
}

@test "Risk Response_customfield_12319746" {
	run grepdumpdata "FIELD\[Risk\ Response\|customfield_12319746\]:"
	check_status
}

@test "Archiver_archivedby" {
	run grepdumpdata "FIELD\[Archiver\|archivedby\]:"
	check_status
}

@test "Hold_customfield_12317326" {
	run grepdumpdata "FIELD\[Hold\|customfield_12317326\]:"
	check_status
}

@test "Watch List_customfield_12319745" {
	run grepdumpdata "FIELD\[Watch\ List\|customfield_12319745\]:"
	check_status
}

@test "RHEL Sub Components_customfield_12317327" {
	run grepdumpdata "FIELD\[RHEL\ Sub\ Components\|customfield_12317327\]:"
	check_status
}

@test "BZ Whiteboard_customfield_12317328" {
	run grepdumpdata "FIELD\[BZ\ Whiteboard\|customfield_12317328\]:"
	check_status
}

@test "Need Info Requestees_customfield_12317370" {
	run grepdumpdata "FIELD\[Need\ Info\ Requestees\|customfield_12317370\]:"
	check_status
}

@test "Product Affects Version_customfield_12317250" {
	run grepdumpdata "FIELD\[Product\ Affects\ Version\|customfield_12317250\]:"
	check_status
}

@test "Feature Link_customfield_12318341" {
	run grepdumpdata "FIELD\[Feature\ Link\|customfield_12318341\]:"
	check_status
}

@test "Git Commit_customfield_12317372" {
	run grepdumpdata "FIELD\[Git\ Commit\|customfield_12317372\]:"
	check_status
}

@test "Major Project_customfield_12320540" {
	run grepdumpdata "FIELD\[Major\ Project\|customfield_12320540\]:"
	check_status
}

@test "Target Milestone_customfield_12317251" {
	run grepdumpdata "FIELD\[Target\ Milestone\|customfield_12317251\]:"
	check_status
}

@test "Cross Team Epic_customfield_12318340" {
	run grepdumpdata "FIELD\[Cross\ Team\ Epic\|customfield_12318340\]:"
	check_status
}

@test "In Portfolio_customfield_12317252" {
	run grepdumpdata "FIELD\[In\ Portfolio\|customfield_12317252\]:"
	check_status
}

@test "MoSCoW_customfield_12316042" {
	run grepdumpdata "FIELD\[MoSCoW\|customfield_12316042\]:"
	check_status
}

@test "Ack'd Status_customfield_12317374" {
	run grepdumpdata "FIELD\[Ack'd\ Status\|customfield_12317374\]:"
	check_status
}

@test "Brief_customfield_12316043" {
	run grepdumpdata "FIELD\[Brief\|customfield_12316043\]:"
	check_status
}

@test "SP-Watchlist_customfield_12317253" {
	run grepdumpdata "FIELD\[SP\-Watchlist\|customfield_12317253\]:"
	check_status
}

@test "Block/Fail - Additional Details_customfield_12317375" {
	run grepdumpdata "FIELD\[Block/Fail\ \-\ Additional\ Details\|customfield_12317375\]:"
	check_status
}

@test "Watchlist Proposed Solution_customfield_12317254" {
	run grepdumpdata "FIELD\[Watchlist\ Proposed\ Solution\|customfield_12317254\]:"
	check_status
}

@test "Shepherd_customfield_12320544" {
	run grepdumpdata "FIELD\[Shepherd\|customfield_12320544\]:"
	check_status
}

@test "Project_project" {
	run grepdumpdata "FIELD\[Project\|project\]:"
	check_status
}

@test "Automated Test_customfield_12320543" {
	run grepdumpdata "FIELD\[Automated\ Test\|customfield_12320543\]:"
	check_status
}

@test "Test Plan Created_customfield_12320542" {
	run grepdumpdata "FIELD\[Test\ Plan\ Created\|customfield_12320542\]:"
	check_status
}

@test "Design Doc Created_customfield_12320541" {
	run grepdumpdata "FIELD\[Design\ Doc\ Created\|customfield_12320541\]:"
	check_status
}

@test "Committed Version_customfield_12320548" {
	run grepdumpdata "FIELD\[Committed\ Version\|customfield_12320548\]:"
	check_status
}

@test "Product Lead_customfield_12320547" {
	run grepdumpdata "FIELD\[Product\ Lead\|customfield_12320547\]:"
	check_status
}

@test "Level of Effort_customfield_12320546" {
	run grepdumpdata "FIELD\[Level\ of\ Effort\|customfield_12320546\]:"
	check_status
}

@test "Resolved_resolutiondate" {
	run grepdumpdata "FIELD\[Resolved\|resolutiondate\]:"
	check_status
}

@test "Interop Bug ID_customfield_12317376" {
	run grepdumpdata "FIELD\[Interop\ Bug\ ID\|customfield_12317376\]:"
	check_status
}

@test "Watchlist Impact_customfield_12317255" {
	run grepdumpdata "FIELD\[Watchlist\ Impact\|customfield_12317255\]:"
	check_status
}

@test "PM Business Priority_customfield_12317256" {
	run grepdumpdata "FIELD\[PM\ Business\ Priority\|customfield_12317256\]:"
	check_status
}

@test "Request Description_customfield_12317377" {
	run grepdumpdata "FIELD\[Request\ Description\|customfield_12317377\]:"
	check_status
}

@test "Customers_customfield_12317257" {
	run grepdumpdata "FIELD\[Customers\|customfield_12317257\]:"
	check_status
}

@test "Resolved Date_customfield_12317379" {
	run grepdumpdata "FIELD\[Resolved\ Date\|customfield_12317379\]:"
	check_status
}

@test "Pool Team_Old_customfield_12317259" {
	run grepdumpdata "FIELD\[Pool\ Team_Old\|customfield_12317259\]:"
	check_status
}

@test "Watchers_watches" {
	run grepdumpdata "FIELD\[Watchers\|watches\]:"
	check_status
}

@test "Triage Status_customfield_12317380" {
	run grepdumpdata "FIELD\[Triage\ Status\|customfield_12317380\]:"
	check_status
}

@test "BZ Status_customfield_12317381" {
	run grepdumpdata "FIELD\[BZ\ Status\|customfield_12317381\]:"
	check_status
}

@test "Dev Approval_customfield_12317260" {
	run grepdumpdata "FIELD\[Dev\ Approval\|customfield_12317260\]:"
	check_status
}

@test "Docs Approval_customfield_12317261" {
	run grepdumpdata "FIELD\[Docs\ Approval\|customfield_12317261\]:"
	check_status
}

@test "Hierarchy Progress Bar_customfield_12317141" {
	run grepdumpdata "FIELD\[Hierarchy\ Progress\ Bar\|customfield_12317141\]:"
	check_status
}

@test "PX Approval_customfield_12317262" {
	run grepdumpdata "FIELD\[PX\ Approval\|customfield_12317262\]:"
	check_status
}

@test "Test Failure Category_customfield_12320551" {
	run grepdumpdata "FIELD\[Test\ Failure\ Category\|customfield_12320551\]:"
	check_status
}

@test "PM Approval_customfield_12317263" {
	run grepdumpdata "FIELD\[PM\ Approval\|customfield_12317263\]:"
	check_status
}

@test "Planning Target_customfield_12319440" {
	run grepdumpdata "FIELD\[Planning\ Target\|customfield_12319440\]:"
	check_status
}

@test "Requires_doc_text_customfield_12317384" {
	run grepdumpdata "FIELD\[Requires_doc_text\|customfield_12317384\]:"
	check_status
}

@test "QE Approval_customfield_12317264" {
	run grepdumpdata "FIELD\[QE\ Approval\|customfield_12317264\]:"
	check_status
}

@test "Goal_customfield_12317386" {
	run grepdumpdata "FIELD\[Goal\|customfield_12317386\]:"
	check_status
}

@test "Start Date_customfield_12317265" {
	run grepdumpdata "FIELD\[Start\ Date\|customfield_12317265\]:"
	check_status
}

@test "Operating System_customfield_12320555" {
	run grepdumpdata "FIELD\[Operating\ System\|customfield_12320555\]:"
	check_status
}

@test "Orchestrator Version_customfield_12320554" {
	run grepdumpdata "FIELD\[Orchestrator\ Version\|customfield_12320554\]:"
	check_status
}

@test "Orchestrator_customfield_12320553" {
	run grepdumpdata "FIELD\[Orchestrator\|customfield_12320553\]:"
	check_status
}

@test "Cluster Flavor_customfield_12320552" {
	run grepdumpdata "FIELD\[Cluster\ Flavor\|customfield_12320552\]:"
	check_status
}

@test "Closed_customfield_12321641" {
	run grepdumpdata "FIELD\[Closed\|customfield_12321641\]:"
	check_status
}

@test "Release Delivery_customfield_12320558" {
	run grepdumpdata "FIELD\[Release\ Delivery\|customfield_12320558\]:"
	check_status
}

@test "Target Backport Versions_customfield_12323940" {
	run grepdumpdata "FIELD\[Target\ Backport\ Versions\|customfield_12323940\]:"
	check_status
}

@test "Docker Version_customfield_12320557" {
	run grepdumpdata "FIELD\[Docker\ Version\|customfield_12320557\]:"
	check_status
}

@test "Delivery Forecast Version_customfield_12320549" {
	run grepdumpdata "FIELD\[Delivery\ Forecast\ Version\|customfield_12320549\]:"
	check_status
}

@test "Partner Team_customfield_12317267" {
	run grepdumpdata "FIELD\[Partner\ Team\|customfield_12317267\]:"
	check_status
}

@test "BZ Devel Whiteboard_customfield_12317268" {
	run grepdumpdata "FIELD\[BZ\ Devel\ Whiteboard\|customfield_12317268\]:"
	check_status
}

@test "Updated_updated" {
	run grepdumpdata "FIELD\[Updated\|updated\]:"
	check_status
}

@test "Need Info From_customfield_12311840" {
	run grepdumpdata "FIELD\[Need\ Info\ From\|customfield_12311840\]:"
	check_status
}

@test "Organization Sponsor_customfield_12316140" {
	run grepdumpdata "FIELD\[Organization\ Sponsor\|customfield_12316140\]:"
	check_status
}

@test "Sponsor_customfield_12317350" {
	run grepdumpdata "FIELD\[Sponsor\|customfield_12317350\]:"
	check_status
}

@test "Product Sponsor_customfield_12316141" {
	run grepdumpdata "FIELD\[Product\ Sponsor\|customfield_12316141\]:"
	check_status
}

@test "Review Deadline_customfield_12317351" {
	run grepdumpdata "FIELD\[Review\ Deadline\|customfield_12317351\]:"
	check_status
}

@test "Severity_customfield_12316142" {
	run grepdumpdata "FIELD\[Severity\|customfield_12316142\]:"
	check_status
}

@test "Strategy Approved_customfield_12317352" {
	run grepdumpdata "FIELD\[Strategy\ Approved\|customfield_12317352\]:"
	check_status
}

@test "Original Estimate_timeoriginalestimate" {
	run grepdumpdata "FIELD\[Original\ Estimate\|timeoriginalestimate\]:"
	check_status
}

@test "Description_description" {
	run grepdumpdata "FIELD\[Description\|description\]:"
	check_status
}

@test "DEV Story Points_customfield_12318444" {
	run grepdumpdata "FIELD\[DEV\ Story\ Points\|customfield_12318444\]:"
	check_status
}

@test "QE Story Points_customfield_12318443" {
	run grepdumpdata "FIELD\[QE\ Story\ Points\|customfield_12318443\]:"
	check_status
}

@test "Regression_customfield_12318446" {
	run grepdumpdata "FIELD\[Regression\|customfield_12318446\]:"
	check_status
}

@test "DOC Story Points_customfield_12318445" {
	run grepdumpdata "FIELD\[DOC\ Story\ Points\|customfield_12318445\]:"
	check_status
}

@test "Market Intelligence_customfield_12317357" {
	run grepdumpdata "FIELD\[Market\ Intelligence\|customfield_12317357\]:"
	check_status
}

@test "Function Impact_customfield_12317358" {
	run grepdumpdata "FIELD\[Function\ Impact\|customfield_12317358\]:"
	check_status
}

@test "Rank (Obsolete)_customfield_12310840" {
	run grepdumpdata "FIELD\[Rank\ \(Obsolete\)\|customfield_12310840\]:"
	check_status
}

@test "Test Blocker_customfield_12318448" {
	run grepdumpdata "FIELD\[Test\ Blocker\|customfield_12318448\]:"
	check_status
}

@test "Automated_customfield_12318447" {
	run grepdumpdata "FIELD\[Automated\|customfield_12318447\]:"
	check_status
}

@test "oVirt Team_customfield_12317359" {
	run grepdumpdata "FIELD\[oVirt\ Team\|customfield_12317359\]:"
	check_status
}

@test "CDW support_ack_customfield_12318449" {
	run grepdumpdata "FIELD\[CDW\ support_ack\|customfield_12318449\]:"
	check_status
}

@test "Summary_summary" {
	run grepdumpdata "FIELD\[Summary\|summary\]:"
	check_status
}

@test "Doc Contact_customfield_12317360" {
	run grepdumpdata "FIELD\[Doc\ Contact\|customfield_12317360\]:"
	check_status
}

@test "Deployment Environment_customfield_12319540" {
	run grepdumpdata "FIELD\[Deployment\ Environment\|customfield_12319540\]:"
	check_status
}

@test "Involved teams_customfield_12317361" {
	run grepdumpdata "FIELD\[Involved\ teams\|customfield_12317361\]:"
	check_status
}

@test "Additional watchers_customfield_12317362" {
	run grepdumpdata "FIELD\[Additional\ watchers\|customfield_12317362\]:"
	check_status
}

@test "Fixed in Build_customfield_12318450" {
	run grepdumpdata "FIELD\[Fixed\ in\ Build\|customfield_12318450\]:"
	check_status
}

@test "External issue URL_customfield_12317242" {
	run grepdumpdata "FIELD\[External\ issue\ URL\|customfield_12317242\]:"
	check_status
}

@test "Fixed In Version_customfield_12317363" {
	run grepdumpdata "FIELD\[Fixed\ In\ Version\|customfield_12317363\]:"
	check_status
}

@test "ServiceNow ID_customfield_12317243" {
	run grepdumpdata "FIELD\[ServiceNow\ ID\|customfield_12317243\]:"
	check_status
}

@test "Testable Builds_customfield_12321740" {
	run grepdumpdata "FIELD\[Testable\ Builds\|customfield_12321740\]:"
	check_status
}

@test "SourceForge Reference_customfield_10002" {
	run grepdumpdata "FIELD\[SourceForge\ Reference\|customfield_10002\]:"
	check_status
}

@test "Gerrit Link_customfield_12317244" {
	run grepdumpdata "FIELD\[Gerrit\ Link\|customfield_12317244\]:"
	check_status
}

@test "ACKs Check_customfield_12317366" {
	run grepdumpdata "FIELD\[ACKs\ Check\|customfield_12317366\]:"
	check_status
}

@test "Mojo Link_customfield_12317245" {
	run grepdumpdata "FIELD\[Mojo\ Link\|customfield_12317245\]:"
	check_status
}

@test "Comment_comment" {
	run grepdumpdata "FIELD\[Comment\|comment\]:"
	check_status
}

@test "Needs Info_customfield_12317246" {
	run grepdumpdata "FIELD\[Needs\ Info\|customfield_12317246\]:"
	check_status
}

@test "[QE] How to address?_customfield_12317367" {
	run grepdumpdata "FIELD\[\[QE\]\ How\ to\ address\?\|customfield_12317367\]:"
	check_status
}

@test "Discussion Needed_customfield_12317247" {
	run grepdumpdata "FIELD\[Discussion\ Needed\|customfield_12317247\]:"
	check_status
}

@test "[QE] Why QE missed?_customfield_12317368" {
	run grepdumpdata "FIELD\[\[QE\]\ Why\ QE\ missed\?\|customfield_12317368\]:"
	check_status
}

@test "CDW docs_ack_customfield_12311941" {
	run grepdumpdata "FIELD\[CDW\ docs_ack\|customfield_12311941\]:"
	check_status
}

@test "Discussion Occurred_customfield_12317248" {
	run grepdumpdata "FIELD\[Discussion\ Occurred\|customfield_12317248\]:"
	check_status
}

@test "RCA Description_customfield_12317369" {
	run grepdumpdata "FIELD\[RCA\ Description\|customfield_12317369\]:"
	check_status
}

@test "Contributing Teams_customfield_12317249" {
	run grepdumpdata "FIELD\[Contributing\ Teams\|customfield_12317249\]:"
	check_status
}

@test "Rank_customfield_12311940" {
	run grepdumpdata "FIELD\[Rank\|customfield_12311940\]:"
	check_status
}

@test "Action_customfield_12317291" {
	run grepdumpdata "FIELD\[Action\|customfield_12317291\]:"
	check_status
}

@test "Dev Target Milestone_customfield_12318141" {
	run grepdumpdata "FIELD\[Dev\ Target\ Milestone\|customfield_12318141\]:"
	check_status
}

@test "Reset contact to default_customfield_12322640" {
	run grepdumpdata "FIELD\[Reset\ contact\ to\ default\|customfield_12322640\]:"
	check_status
}

@test "prev_assignee_customfield_12318140" {
	run grepdumpdata "FIELD\[prev_assignee\|customfield_12318140\]:"
	check_status
}

@test "Biz Program Manager_customfield_12318143" {
	run grepdumpdata "FIELD\[Biz\ Program\ Manager\|customfield_12318143\]:"
	check_status
}

@test "PLM  Technical Lead_customfield_12318142" {
	run grepdumpdata "FIELD\[PLM\ \ Technical\ Lead\|customfield_12318142\]:"
	check_status
}

@test "Planned Start_customfield_12317296" {
	run grepdumpdata "FIELD\[Planned\ Start\|customfield_12317296\]:"
	check_status
}

@test "Product Page link_customfield_12318145" {
	run grepdumpdata "FIELD\[Product\ Page\ link\|customfield_12318145\]:"
	check_status
}

@test "Solution_customfield_12317298" {
	run grepdumpdata "FIELD\[Solution\|customfield_12317298\]:"
	check_status
}

@test "Tech Program Manager_customfield_12318144" {
	run grepdumpdata "FIELD\[Tech\ Program\ Manager\|customfield_12318144\]:"
	check_status
}

@test "Fix Version/s_fixVersions" {
	run grepdumpdata "FIELD\[Fix\ Version/s\|fixVersions\]:"
	check_status
}

@test "Reminder Date_customfield_12317290" {
	run grepdumpdata "FIELD\[Reminder\ Date\|customfield_12317290\]:"
	check_status
}

@test "Test Work Items_customfield_12312840" {
	run grepdumpdata "FIELD\[Test\ Work\ Items\|customfield_12312840\]:"
	check_status
}

@test "Internal Product/Project names_customfield_12318147" {
	run grepdumpdata "FIELD\[Internal\ Product/Project\ names\|customfield_12318147\]:"
	check_status
}

@test "Latest Status Summary_customfield_12317299" {
	run grepdumpdata "FIELD\[Latest\ Status\ Summary\|customfield_12317299\]:"
	check_status
}

@test "Portal Product Name_customfield_12318146" {
	run grepdumpdata "FIELD\[Portal\ Product\ Name\|customfield_12318146\]:"
	check_status
}

@test "QE Test Coverage_customfield_12312848" {
	run grepdumpdata "FIELD\[QE\ Test\ Coverage\|customfield_12312848\]:"
	check_status
}

@test "Stale Date_customfield_12318148" {
	run grepdumpdata "FIELD\[Stale\ Date\|customfield_12318148\]:"
	check_status
}

@test "Approver_customfield_12318150" {
	run grepdumpdata "FIELD\[Approver\|customfield_12318150\]:"
	check_status
}

@test "Internal Target Milestone numeric_customfield_12321440" {
	run grepdumpdata "FIELD\[Internal\ Target\ Milestone\ numeric\|customfield_12321440\]:"
	check_status
}

@test "DevOps Discussion Occurred_customfield_12319241" {
	run grepdumpdata "FIELD\[DevOps\ Discussion\ Occurred\|customfield_12319241\]:"
	check_status
}

@test "EAP PT Cross Product Agreement (CPA)_customfield_12321441" {
	run grepdumpdata "FIELD\[EAP\ PT\ Cross\ Product\ Agreement\ \(CPA\)\|customfield_12321441\]:"
	check_status
}

@test "MVP Status_customfield_12318152" {
	run grepdumpdata "FIELD\[MVP\ Status\|customfield_12318152\]:"
	check_status
}

@test "Organization ID_customfield_12323741" {
	run grepdumpdata "FIELD\[Organization\ ID\|customfield_12323741\]:"
	check_status
}

@test "Software_customfield_12323740" {
	run grepdumpdata "FIELD\[Software\|customfield_12323740\]:"
	check_status
}

@test "Design Review Sign-off_customfield_12319242" {
	run grepdumpdata "FIELD\[Design\ Review\ Sign\-off\|customfield_12319242\]:"
	check_status
}

@test "Risk Impact_customfield_12318156" {
	run grepdumpdata "FIELD\[Risk\ Impact\|customfield_12318156\]:"
	check_status
}

@test "Risk Likelihood_customfield_12318155" {
	run grepdumpdata "FIELD\[Risk\ Likelihood\|customfield_12318155\]:"
	check_status
}

@test "Priority_priority" {
	run grepdumpdata "FIELD\[Priority\|priority\]:"
	check_status
}

@test "Impacts_customfield_12313940" {
	run grepdumpdata "FIELD\[Impacts\|customfield_12313940\]:"
	check_status
}

@test "Security Sensitive Issue_customfield_12311640" {
	run grepdumpdata "FIELD\[Security\ Sensitive\ Issue\|customfield_12311640\]:"
	check_status
}

@test "Involved_customfield_12311641" {
	run grepdumpdata "FIELD\[Involved\|customfield_12311641\]:"
	check_status
}

@test "Affects Version/s_versions" {
	run grepdumpdata "FIELD\[Affects\ Version/s\|versions\]:"
	check_status
}

@test "Next Planned Release Date_customfield_12319247" {
	run grepdumpdata "FIELD\[Next\ Planned\ Release\ Date\|customfield_12319247\]:"
	check_status
}

@test "Risk Mitigation Strategy_customfield_12318158" {
	run grepdumpdata "FIELD\[Risk\ Mitigation\ Strategy\|customfield_12318158\]:"
	check_status
}

@test "Risk Score Assessment_customfield_12318157" {
	run grepdumpdata "FIELD\[Risk\ Score\ Assessment\|customfield_12318157\]:"
	check_status
}

@test "Avoidable_customfield_12319249" {
	run grepdumpdata "FIELD\[Avoidable\|customfield_12319249\]:"
	check_status
}

@test "Target end_customfield_12313942" {
	run grepdumpdata "FIELD\[Target\ end\|customfield_12313942\]:"
	check_status
}

@test "Target start_customfield_12313941" {
	run grepdumpdata "FIELD\[Target\ start\|customfield_12313941\]:"
	check_status
}

@test "BZ Devel Conditional NAK_customfield_12317270" {
	run grepdumpdata "FIELD\[BZ\ Devel\ Conditional\ NAK\|customfield_12317270\]:"
	check_status
}

@test "CDW Resolution_customfield_12317392" {
	run grepdumpdata "FIELD\[CDW\ Resolution\|customfield_12317392\]:"
	check_status
}

@test "mvp_customfield_12317271" {
	run grepdumpdata "FIELD\[mvp\|customfield_12317271\]:"
	check_status
}

@test "Key_issuekey" {
	run grepdumpdata "FIELD\[Key\|issuekey\]:"
	check_status
}

@test "rpl_customfield_12317272" {
	run grepdumpdata "FIELD\[rpl\|customfield_12317272\]:"
	check_status
}

@test "Verified_customfield_12317273" {
	run grepdumpdata "FIELD\[Verified\|customfield_12317273\]:"
	check_status
}

@test "Documenter_customfield_12318241" {
	run grepdumpdata "FIELD\[Documenter\|customfield_12318241\]:"
	check_status
}

@test "ITR-ITM_customfield_12317396" {
	run grepdumpdata "FIELD\[ITR\-ITM\|customfield_12317396\]:"
	check_status
}

@test "Analyst_customfield_12318243" {
	run grepdumpdata "FIELD\[Analyst\|customfield_12318243\]:"
	check_status
}

@test "Internal Target Release and Milestone_customfield_12317277" {
	run grepdumpdata "FIELD\[Internal\ Target\ Release\ and\ Milestone\|customfield_12317277\]:"
	check_status
}

@test "Current Deadline_customfield_12317278" {
	run grepdumpdata "FIELD\[Current\ Deadline\|customfield_12317278\]:"
	check_status
}

@test "Global Practices Lead_customfield_12318245" {
	run grepdumpdata "FIELD\[Global\ Practices\ Lead\|customfield_12318245\]:"
	check_status
}

@test "Current Deadline Type_customfield_12317279" {
	run grepdumpdata "FIELD\[Current\ Deadline\ Type\|customfield_12317279\]:"
	check_status
}

@test "Eng. priority_customfield_12312940" {
	run grepdumpdata "FIELD\[Eng\.\ priority\|customfield_12312940\]:"
	check_status
}

@test "QE priority_customfield_12312941" {
	run grepdumpdata "FIELD\[QE\ priority\|customfield_12312941\]:"
	check_status
}

@test "Embargo Override_customfield_12317281" {
	run grepdumpdata "FIELD\[Embargo\ Override\|customfield_12317281\]:"
	check_status
}

@test "Baseline Start_customfield_12317282" {
	run grepdumpdata "FIELD\[Baseline\ Start\|customfield_12317282\]:"
	check_status
}

@test "Preliminary Testing_customfield_12321540" {
	run grepdumpdata "FIELD\[Preliminary\ Testing\|customfield_12321540\]:"
	check_status
}

@test "UXD Design[Test]_customfield_12319340" {
	run grepdumpdata "FIELD\[UXD\ Design\[Test\]\|customfield_12319340\]:"
	check_status
}

@test "Watchers Groups_customfield_12323840" {
	run grepdumpdata "FIELD\[Watchers\ Groups\|customfield_12323840\]:"
	check_status
}

@test "Baseline End_customfield_12317283" {
	run grepdumpdata "FIELD\[Baseline\ End\|customfield_12317283\]:"
	check_status
}

@test "EAP PT Feature Implementation (FI)_customfield_12317041" {
	run grepdumpdata "FIELD\[EAP\ PT\ Feature\ Implementation\ \(FI\)\|customfield_12317041\]:"
	check_status
}

@test "Errata Link_customfield_12321541" {
	run grepdumpdata "FIELD\[Errata\ Link\|customfield_12321541\]:"
	check_status
}

@test "Docs Analysis_customfield_12317042" {
	run grepdumpdata "FIELD\[Docs\ Analysis\|customfield_12317042\]:"
	check_status
}

@test "Subproject_customfield_12317284" {
	run grepdumpdata "FIELD\[Subproject\|customfield_12317284\]:"
	check_status
}

@test "Root Cause_customfield_12317285" {
	run grepdumpdata "FIELD\[Root\ Cause\|customfield_12317285\]:"
	check_status
}

@test "Stage Links_customfield_12317043" {
	run grepdumpdata "FIELD\[Stage\ Links\|customfield_12317043\]:"
	check_status
}

@test "Docs Pull Request_customfield_12317044" {
	run grepdumpdata "FIELD\[Docs\ Pull\ Request\|customfield_12317044\]:"
	check_status
}

@test "Project/s_customfield_12317286" {
	run grepdumpdata "FIELD\[Project/s\|customfield_12317286\]:"
	check_status
}

@test "Σ Progress_aggregateprogress" {
	run grepdumpdata "FIELD\[Σ\ Progress\|aggregateprogress\]:"
	check_status
}

@test "Authorized Party_customfield_12321542" {
	run grepdumpdata "FIELD\[Authorized\ Party\|customfield_12321542\]:"
	check_status
}

@test "User Story_customfield_12311740" {
	run grepdumpdata "FIELD\[User\ Story\|customfield_12311740\]:"
	check_status
}

@test "Reminder Frequency_customfield_12317288" {
	run grepdumpdata "FIELD\[Reminder\ Frequency\|customfield_12317288\]:"
	check_status
}

@test "QE Acceptance Test Link_customfield_12311741" {
	run grepdumpdata "FIELD\[QE\ Acceptance\ Test\ Link\|customfield_12311741\]:"
	check_status
}

@test "Partner Fixed Version_customfield_12322440" {
	run grepdumpdata "FIELD\[Partner\ Fixed\ Version\|customfield_12322440\]:"
	check_status
}

@test "Scoping Status_customfield_12319272" {
	run grepdumpdata "FIELD\[Scoping\ Status\|customfield_12319272\]:"
	check_status
}

@test "QE_AUTO_Coverage_customfield_12319271" {
	run grepdumpdata "FIELD\[QE_AUTO_Coverage\|customfield_12319271\]:"
	check_status
}

@test "Function_customfield_12319274" {
	run grepdumpdata "FIELD\[Function\|customfield_12319274\]:"
	check_status
}

@test "Stakeholders_customfield_12319273" {
	run grepdumpdata "FIELD\[Stakeholders\|customfield_12319273\]:"
	check_status
}

@test "Workstream_customfield_12319275" {
	run grepdumpdata "FIELD\[Workstream\|customfield_12319275\]:"
	check_status
}

@test "Version_customfield_12319278" {
	run grepdumpdata "FIELD\[Version\|customfield_12319278\]:"
	check_status
}

@test "CVSS Score_customfield_12324748" {
	run grepdumpdata "FIELD\[CVSS\ Score\|customfield_12324748\]:"
	check_status
}

@test "CWE ID_customfield_12324747" {
	run grepdumpdata "FIELD\[CWE\ ID\|customfield_12324747\]:"
	check_status
}

@test "CVE ID_customfield_12324749" {
	run grepdumpdata "FIELD\[CVE\ ID\|customfield_12324749\]:"
	check_status
}

@test "End Date_customfield_12324744" {
	run grepdumpdata "FIELD\[End\ Date\|customfield_12324744\]:"
	check_status
}

@test "Security Documentation Type_customfield_12319270" {
	run grepdumpdata "FIELD\[Security\ Documentation\ Type\|customfield_12319270\]:"
	check_status
}

@test "Source_customfield_12324746" {
	run grepdumpdata "FIELD\[Source\|customfield_12324746\]:"
	check_status
}

@test "Git Pull Request_customfield_12310220" {
	run grepdumpdata "FIELD\[Git\ Pull\ Request\|customfield_12310220\]:"
	check_status
}

@test "ID_customfield_12319279" {
	run grepdumpdata "FIELD\[ID\|customfield_12319279\]:"
	check_status
}

@test "Upstream Affected Component_customfield_12324751" {
	run grepdumpdata "FIELD\[Upstream\ Affected\ Component\|customfield_12324751\]:"
	check_status
}

@test "Embargo Status_customfield_12324750" {
	run grepdumpdata "FIELD\[Embargo\ Status\|customfield_12324750\]:"
	check_status
}

@test "Products_customfield_12319040" {
	run grepdumpdata "FIELD\[Products\|customfield_12319040\]:"
	check_status
}

@test "Images_thumbnail" {
	run grepdumpdata "FIELD\[Images\|thumbnail\]:"
	check_status
}

@test "Special Handling_customfield_12324753" {
	run grepdumpdata "FIELD\[Special\ Handling\|customfield_12324753\]:"
	check_status
}

@test "Downstream Component Name_customfield_12324752" {
	run grepdumpdata "FIELD\[Downstream\ Component\ Name\|customfield_12324752\]:"
	check_status
}

@test "Test Link_customfield_12325840" {
	run grepdumpdata "FIELD\[Test\ Link\|customfield_12325840\]:"
	check_status
}

@test "Docs Impact Notes_customfield_12319287" {
	run grepdumpdata "FIELD\[Docs\ Impact\ Notes\|customfield_12319287\]:"
	check_status
}

@test "Docs Impact_customfield_12319286" {
	run grepdumpdata "FIELD\[Docs\ Impact\|customfield_12319286\]:"
	check_status
}

@test "Created_created" {
	run grepdumpdata "FIELD\[Created\|created\]:"
	check_status
}

@test "Marketing Impact Notes_customfield_12319289" {
	run grepdumpdata "FIELD\[Marketing\ Impact\ Notes\|customfield_12319289\]:"
	check_status
}

@test "GtmhubTaskParentType_customfield_12321240" {
	run grepdumpdata "FIELD\[GtmhubTaskParentType\|customfield_12321240\]:"
	check_status
}

@test "Marketing Impact_customfield_12319288" {
	run grepdumpdata "FIELD\[Marketing\ Impact\|customfield_12319288\]:"
	check_status
}

@test "Impact Rating_customfield_12324755" {
	run grepdumpdata "FIELD\[Impact\ Rating\|customfield_12324755\]:"
	check_status
}

@test "Errata ID_customfield_12324754" {
	run grepdumpdata "FIELD\[Errata\ ID\|customfield_12324754\]:"
	check_status
}

@test "Docs QE Status_customfield_12310230" {
	run grepdumpdata "FIELD\[Docs\ QE\ Status\|customfield_12310230\]:"
	check_status
}

@test "Migration Text_customfield_12313740" {
	run grepdumpdata "FIELD\[Migration\ Text\|customfield_12313740\]:"
	check_status
}

@test "Communication Breakdown_customfield_12319250" {
	run grepdumpdata "FIELD\[Communication\ Breakdown\|customfield_12319250\]:"
	check_status
}

@test "affectsRHMIVersion_customfield_12318040" {
	run grepdumpdata "FIELD\[affectsRHMIVersion\|customfield_12318040\]:"
	check_status
}

@test "Product Operations Engineering Contact_customfield_12322540" {
	run grepdumpdata "FIELD\[Product\ Operations\ Engineering\ Contact\|customfield_12322540\]:"
	check_status
}

@test "Release Milestone_customfield_12319252" {
	run grepdumpdata "FIELD\[Release\ Milestone\|customfield_12319252\]:"
	check_status
}

@test "QE Properly Involved_customfield_12319251" {
	run grepdumpdata "FIELD\[QE\ Properly\ Involved\|customfield_12319251\]:"
	check_status
}

@test "Strategic Alignment_customfield_12324840" {
	run grepdumpdata "FIELD\[Strategic\ Alignment\|customfield_12324840\]:"
	check_status
}

@test "affectsRHOAMVersion_customfield_12318041" {
	run grepdumpdata "FIELD\[affectsRHOAMVersion\|customfield_12318041\]:"
	check_status
}

@test "Bugzilla References_customfield_12310440" {
	run grepdumpdata "FIELD\[Bugzilla\ References\|customfield_12310440\]:"
	check_status
}

@test "Security Level_security" {
	run grepdumpdata "FIELD\[Security\ Level\|security\]:"
	check_status
}

@test "Attachment_attachment" {
	run grepdumpdata "FIELD\[Attachment\|attachment\]:"
	check_status
}

@test "Delivery Mode_customfield_12323640" {
	run grepdumpdata "FIELD\[Delivery\ Mode\|customfield_12323640\]:"
	check_status
}

@test "VEX Justification_customfield_12325940" {
	run grepdumpdata "FIELD\[VEX\ Justification\|customfield_12325940\]:"
	check_status
}

@test "Chapter #_customfield_12323642" {
	run grepdumpdata "FIELD\[Chapter\ \#\|customfield_12323642\]:"
	check_status
}

@test "Proposed Initiative_customfield_12319263" {
	run grepdumpdata "FIELD\[Proposed\ Initiative\|customfield_12319263\]:"
	check_status
}

@test "Keyword_customfield_12319262" {
	run grepdumpdata "FIELD\[Keyword\|customfield_12319262\]:"
	check_status
}

@test "Workaround_customfield_12323641" {
	run grepdumpdata "FIELD\[Workaround\|customfield_12323641\]:"
	check_status
}

@test "Immutable Due Date_customfield_12319264" {
	run grepdumpdata "FIELD\[Immutable\ Due\ Date\|customfield_12319264\]:"
	check_status
}

@test "Failure Category_customfield_12319267" {
	run grepdumpdata "FIELD\[Failure\ Category\|customfield_12319267\]:"
	check_status
}

@test "Epic Color_customfield_12323648" {
	run grepdumpdata "FIELD\[Epic\ Color\|customfield_12323648\]:"
	check_status
}

@test "Language_customfield_12323647" {
	run grepdumpdata "FIELD\[Language\|customfield_12323647\]:"
	check_status
}

@test "RH Private Keywords_customfield_12323649" {
	run grepdumpdata "FIELD\[RH\ Private\ Keywords\|customfield_12323649\]:"
	check_status
}

@test "Section ID_customfield_12323644" {
	run grepdumpdata "FIELD\[Section\ ID\|customfield_12323644\]:"
	check_status
}

@test "Section Title_customfield_12323643" {
	run grepdumpdata "FIELD\[Section\ Title\|customfield_12323643\]:"
	check_status
}

@test "URL_customfield_12323646" {
	run grepdumpdata "FIELD\[URL\|customfield_12323646\]:"
	check_status
}

@test "Reporter RHN ID_customfield_12323645" {
	run grepdumpdata "FIELD\[Reporter\ RHN\ ID\|customfield_12323645\]:"
	check_status
}

@test "Notes_customfield_12313841" {
	run grepdumpdata "FIELD\[Notes\|customfield_12313841\]:"
	check_status
}

@test "sprint_count_customfield_12319269" {
	run grepdumpdata "FIELD\[sprint_count\|customfield_12319269\]:"
	check_status
}

@test "QE portion_customfield_12319268" {
	run grepdumpdata "FIELD\[QE\ portion\|customfield_12319268\]:"
	check_status
}

@test "Release Note Status_customfield_12310213" {
	run grepdumpdata "FIELD\[Release\ Note\ Status\|customfield_12310213\]:"
	check_status
}

@test "Writer_customfield_12310214" {
	run grepdumpdata "FIELD\[Writer\|customfield_12310214\]:"
	check_status
}

