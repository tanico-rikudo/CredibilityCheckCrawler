function get_linklist(){
	link_list = document.links
	return link_list
}
function get_linklist_length(){
	link_list = document.links
	return link_list.length
}
function replace_link(str_no,real_url){
	// console.log(str_no)
	// console.log(document.links[parseInt(str_no)].href)
	document.links[parseInt(str_no)].href = real_url
	// console.log(document.links[parseInt(str_no)].href)
}