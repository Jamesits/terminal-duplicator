function openViedo() {
        var args = window.location.href.split("?"),
            key = '830a3da68719424daa597d5a84de2d9d',
            channel = "10086",
            videoChecked = true,
            audioChecked = true,
            username = '',
            members = 0,
            videoDpi = '120p_1',
            videoDevice = '',
            audioDevice = 'default',
            uid = undefined,
            disableAudio = false,
            disableVideo = false,
            viewSwitch = false,
            remoteStremList = {},
            client, localStream;


        /* initialzed, join channel */
        (function initAgoraRTC() {
            //document.getElementById("video").disabled = true;
            console.log('Joining channel ' + key + ' : ' + channel);
            client = AgoraRTC.createClient();


            client.init(key, function () {
                console.log("AgoraRTC client initialized");
                var token = undefined;
                client.join(channel, undefined, function (uid) {
                    console.log("User " + uid + " join channel successfully");
                    localStream = initLocalStream(uid);
                },
                    function (err) {
                        console.log("Join channel failed", err);
                    });
            }, function (err) {
                console.log("AgoraRTC client init failed", err);
                alert(err);
                window.location.href = "../";
            });
        } ());

        subscribeSdkEvents();
        // subscribeDomEvents();

        (function updateChannelList() {
            /* get history channel */
            var channelList = localStorage.getItem("channelList");
            channelList = channelList ? channelList.split(",") : [];
            if (channelList.indexOf(channel) == -1) {
                channelList.push(channel);
            }
            channelList.forEach(function (e, index) {
                var $li = '<li data-channel="' + e + '"><img src="images/voice_index_three.png" /><label>' + e;
                if (e === channel) {
                    $li += '<span class="color">(In Conferencing)</span>';
                }
                $li += '</label></li>'
                $(".menu_content ul").append($li);
            });
            localStorage.setItem("channelList", channelList.join(","))
        } ());
        /* Initialize end */

        /********************* Utility functions begins *************************/
        function subscribeSdkEvents() {
            client.on('stream-added', function (evt) {
                var stream = evt.stream;
                console.log("New stream added: " + stream.getId());
                console.log("Subscribe ", stream);
                client.subscribe(stream, function (err) {
                    console.log("Subscribe stream failed", err);
                });
            });

            client.on('peer-leave', function (evt) {
                var stream = evt.stream;
                var $p = $('<p id="infoStream' + evt.uid + '">' + evt.uid + ' quit from room</p>');
                $(".info").append($p);
                setTimeout(function () { $p.remove(); }, 10 * 1000);
                delete remoteStremList[evt.uid];
                stream.stop();
                console.log($("#agora_remote" + evt.uid).length);
                if ($("#agora_remote" + evt.uid).length > 0) {
                    $("#agora_remote" + evt.uid).parent().remove();
                }
            });

            client.on('stream-removed', function (evt) {
                var stream = evt.stream;
                var $p = $('<p id="infoStream' + stream.getId() + '">' + stream.getId() + ' quit from room</p>');
                $(".info").append($p);
                setTimeout(function () { $p.remove(); }, 10 * 1000);
                delete remoteStremList[stream.getId()];
                stream.stop();
                if ($("#agora_remote" + stream.getId()).length > 0) {
                    $("#agora_remote" + stream.getId()).parent().remove();
                }
            });

            client.on('stream-subscribed', function (evt) {
                var stream = evt.stream;
                console.log("Catch stream-subscribed event");
                console.log("Subscribe remote stream successfully: " + stream.getId());
                console.log(evt);
                // displayInfo(stream);
                remoteStremList[stream.getId()] = stream;
                members = 0;
                for (var key in remoteStremList) {
                    members += 1;
                }
                $(".content").hide();
                members == 1 ? timedCount() : null;
                var $container = viewSwitch ? $(".left ul") : $(".right ul");
                if (!videoChecked) {
                    $(".screen").removeClass("wait").addClass("audio");
                    $container.append('<li class="remoteAudio"><div id="agora_remote' + stream.getId() + '"></div><p>' + stream.getId() + '</p></li>')
                    stream.play('agora_remote' + stream.getId());
                    $("#agora_remote" + stream.getId() + " div").hide();
                    return;
                }
                if (members == 1) {
                    $(".screen").removeClass("wait").addClass("video single");
                }
                else {
                    $(".screen").removeClass("wait single").addClass("video");
                    viewSwitch ? null : $(".screen").addClass("multi");
                }
                if (stream.video) {
                    $container.append('<li class="remoteVideo"><div id="agora_remote' + stream.getId() + '"></div></li>');
                }
                else {
                    $container.append('<li class="remoteAudio"><div class="audioImg" id="agora_remote' + stream.getId() + '"></div><p>' + stream.getId() + '</p></li>');
                    $("#agora_remote" + stream.getId() + " div").hide();
                }
                stream.play('agora_remote' + stream.getId());
            });
        }

        function initLocalStream(id, callback) {
            uid = id || uid;
            if (localStream) {
                console.log("localStream exists");
                client.unpublish(localStream, function (err) {
                    console.log("unpublish localStream fail.", err);
                });
                localStream.close();
            }

            window.local = localStream = AgoraRTC.createStream({
                streamID: uid,
                audio: true,
                video: videoChecked,
                screen: true,
                cameraId: videoDevice,
                microphoneId: audioDevice
            });
            if (videoChecked) {
                localStream.setVideoProfile(videoDpi);
            }

            localStream.init(function () {
                console.log("getUserMedia successfully");
                console.log(localStream);
                localStream.play('local');
                // if (!videoChecked) {
                //     $(".screen .left div").addClass("waitAudio");
                //     $("#local div").hide();
                //
                // }
                // else {
                //     if (viewSwitch) {
                //         $(".right ul").html('');
                //         $(".right ul").append('<li class="remoteVideo"><div id="agora_remote' + localStream.getId() + '"></div></li>');
                //         // localStream.play('agora_remote' + localStream.getId());
                //     }
                //     else {
                //         $(".left").html('<div class="" id="local"></div>');
                //         // localStream.play("local");
                //     }
                // }

                client.publish(localStream, function (err) {
                    console.log("Publish local stream error: " + err);
                });
                client.on('stream-published', function (evt) {
                console.log("Publish local stream successfully");
                });
            },
                function (err) {
                    console.log("getUserMedia failed", err);
                });
            return localStream;
        }

        
        /* Utility functions end */
    }