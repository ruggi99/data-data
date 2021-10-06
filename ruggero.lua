obs = obslua

function script_description()
	return "Plugin del Ruggio"
end

function script_load()
	local sources = obs.obs_enum_sources()
	if sources ~= nil then
		for _, source in ipairs(sources) do
			local source_id = obs.obs_source_get_id(source)
			local privates = obs.obs_source_get_private_settings(source)
			if source_id == "wasapi_input_capture" or
				source_id == "ffmpeg_source" or
				source_id == "vlc_source" then
				obs.obs_data_set_bool(privates, "mixer_hidden", false)
				--obs.obs_source_set_muted(source, false)
			else
				obs.obs_data_set_bool(privates, "mixer_hidden", true)
				obs.obs_source_set_muted(source, true)
			end
			obs.obs_data_release(privates)
		end
	end

	obs.source_list_release(sources)
end