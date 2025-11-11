# Take video file url, or http url as input
# for http url, return not implement
# take the video file url
# check if the corresponding audio file is present
# video file .mp4 , audio file .m4a or .mp3

# now we will build a crew agentic system
# First we will create an id for the run
# And we need access to shared memory, so that
# we don't depend on llm output to get things like ids
# ids should be simple enough, <job_type>_<5_numbers>_<5_characters>

## Agents

### Audio Handler
# which looks at the file, inspects it
# converts it to mp3 if needed
# save the mp3, and conversion status to true, along with path
# if not present it tries to generate one from the video


### Transcription
# one uses whisper base-en locally
# to transcribe the audio in parts
# and give back the transcription
# as a result, the transcription should be
# saved to database, and if the tool is invoked
# again, for the same run, then it won't need
# to transcribe again
# the transcription should have proper timestamp
# and has to be parsed into a structure

### Vision

# depending on the transcription
# let the agent decide, at which points
# it needs to look at the images.
# so the agent needs to analyse in batches
# statements like in this frame, or montages where 
# scenes need to be analysed, sometime dialogues are 
# not needed, but maybe if something is about to happen
# like confrontation, we may need to confirm what is
# the situation
# 
# It has access to a bunch of tools for analysis
# images extracted should be in jpeg, with a max of 1024x1024
# preserving the aspect ratio of the original

# there can be more than 1 loop of this
# because we will analyse in batches
# initially, we can do it sequentially
# so we pass back a summary of the previous frame
# the analyser agent can go back to the frame retriever
# to get specific details about the image.
# in case its a cluster of image
# we can use libvips to make a grid collage
# and pass it to the llm call, the question framed by llm

### Vision Tools

## ffmpeg 

# It calls ffmpeg, to get the frames within the
# duration, gets back the thumnail image file locations
# (this is not passed directly to agents)
# (its used internally by other agents)

## image_analyzer

# used by agents to get better understanding
# of the images

## scene_analyzer

# receives a timeframe with respect to the video
# uses ffmpeg to get frames
# uses libvips or equivalent to merge them into a grid collage
# send the image base64, instructions on the image sequence
# question posed by the llm
# the files are saved, with their timestamps with respect to the whole video
# so similar requests, the frames should not be recreated,
# only missing ones
# this can be put into its own module, and scene analyzer can use
# it as library
# the store can also be polymorphic
# when used with file store, it can create hiearchial file names

# in case the video is describing, say an art style
# then it should be able to understand to look at the image
# with maybe 200-500ms on either side to understand

# when talking about concepts, in the image/video
# that would also signify it needs to look at the image

# this can be different for other cases.
# if this can't be generic, then it can be injectable
# breakdown analyser. doing a analysis of breakdown style videos

### transcriber

# this agent will help extract out audio segement data
# when requested
# it can accept a time-range
# and check if data is available, then return it back
# since there is only one audio for 1 video
# one can easily find the exact audio file
# whisper-local is an option, we can resort to litellLM's transcription
# with its library, it comes from crew. but crew doesn't support it


## glossary

# this would be responsible for managing shared state
# agents can ask questions while processing the
# transcripts for better understanding
# for ex: a bunch of frames has already been analysed 
#         while looking for colors and leading lines
#         next time the llm reads 'chromatic abberation'
#         the model could ask for the colors used and in which frames
#         And the question would be passed down to the tool
#         The tool will do query refinement and look at the
#         store for answers. If not found delegate to analyser agents

# # given that we have been storing polymorphically
# either a database or file based index or id search
# or a combination
# we would need to be able to search if certain things
# are already present
# this would help query different sources
# how to query, the prompt should be specific to the source
# in use, coupled to it
# Instructions on how to search
# If its DB, then the prompt should be injected with
# what is the schema, and what queries to use and sanity check
# of deletes, maybe trying prepared statement

# The Store is shared scratchpad
# in case we have keys or ids, they can be accessed
# it can be in memory, json, file, database.

## the transformer
# this is the last agent in chain which is injected
# we will call this a polymorphic analyser agent
# for present case, we need to look at art-style
# breakdown video, called graphic reduction
# analyse, big-small-medium, chromatic abberations
# etc.
# And then convert it into an art-style in a textual format
# removing references of the source and inspirations