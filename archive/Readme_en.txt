----------------------------------------------------------------
----------------------------------------------------------------

　PmxDressup

　　ver1.00.00

　　　　　　　　　　　　　　　　　miu200521358

----------------------------------------------------------------
----------------------------------------------------------------


　Thank you for downloading my work.
　Please check the following before using it.

----------------------------------------------------------------


----------------------------------------------------------------
■ Summary
----------------------------------------------------------------

　This tool fits a specified costume to a specified model according to her body shape.

　Automatic fitting based on bone length and body thickness
　The figure material can be made translucent, allowing for detailed adjustment while checking the body shape.
　Adjustment of bones and rigid body/joint relationships for output of changeover results.
　Color matching and copying of settings for each material.

　The following bones will be created for the changeover model
　　All parents, upper body 2, arm twist, hand twist, toes EX

　[Work required in advance]
　　If there are vertices in the same material that you want to output and those that you do not want to output, please separate the materials.

　[Manual adjustment after output]
　　Set the rigid body group and non-collision group.
　　　　→ If the costume is to be violent, set the rigid body at the base of the costume to be non-collision with the rigid body of the body it is in contact with.
　　Delete lower vertex
　　　　→ Delete vertices as long as they do not cause holes in the model, so that vertices do not penetrate the model and the model becomes lighter.

　【Notes】
　　The weights of the costume models have been slightly altered to clean up the deformation.
　　　This product is not available for costume models for which weight manipulation is not permitted.
　　If the mesh on the arms or other body-covering positions of the costume is weighted with weights other than the quasi-standard bones, it will not be eligible for support
   (I follow up to some extent, but there will be many cases where you will be asked to manipulate the semi-standardized bones and play with the scale, etc.)


----------------------------------------------------------------
Video distribution
----------------------------------------------------------------

YouTube
https://youtu.be/_4Ikx19ISjA

NicoNico Douga
https://www.nicovideo.jp/watch/sm42645182


----------------------------------------------------------------
Included files
----------------------------------------------------------------

　PmxDressup_x.xx.xx.exe ... Tool itself (with language-specific batchs)
　Readme.txt ... Readme
　VMD Sizing Wiki ... Link to Wiki
　Content tree still image ... Link to content tree still image
　Body for mesh filling ... Body (made by VRoid)


----------------------------------------------------------------
Operating environment
----------------------------------------------------------------

　Windows 10/11 64bit
　CPU or GPU running OpenGL 4.4 or higher


----------------------------------------------------------------
Startup
----------------------------------------------------------------

Basically, you can start the exe as it is.

For translated versions, double-click on the appropriate language batch.
　English version ... -en.bat
　Simplified Chinese version ... -zh.bat
　Korean version ... -ko.bat

The file history can be transferred by copying and pasting "history.json" into the same hierarchy as the exe.


----------------------------------------------------------------
■　Basic Usage
----------------------------------------------------------------

 1. in the File tab, specify the person model and costume model (motion is optional but heavy...)

 2. open the Settings tab
    - Once you open the settings tab, you can press the output button. 3.

 3. In the Settings tab, the left side of the screen shows the model with basic fitting (height, build, etc.) done.
    - In the upper right (left), you can specify whether or not to output the material by its opacity.
       - Materials with opacity less than 1 will not be output, so please lower the opacity of materials you do not need.

    - In the upper right corner (right), you can specify whether or not to apply morphs to the person and costume models.
       - The upper right corner (right) allows you to specify the morph to be applied to the person and costume model.

    - In the lower right corner, you can make adjustments for each bone type
       - Scale X ... Up direction to the direction of the bone
       - Scale Y ... in the direction of the bone
       - Scale Z ... depth relative to the direction of the bone

       - Rotation X ... back and forth relative to the direction of the bone
       - Rotation Y ... in the direction of the bone (torsional rotation)
       - Rotation Z ... vertical with respect to the direction of the bone

       - Move X ... Global X direction
       - Move Y ... global Y direction
       - Move Z ... Global Z direction

    - If there is a mesh with the same bone name but with weights applied to both the person and the costume, the position of the mesh will basically be output according to the person's side.
      However, if you check the box "Bone positions are aligned with costume model", you can force the output to be aligned with the bone positions on the costume side.
      (Especially from the wrist to the tips of the fingers, no fitting is performed, so please select accordingly.)

    - Color matching can be done for each material of the person or costume.
       - Paint icons ... Extract colors from the screen like an eyedropper and specify colors.
       - Color Bar Direct ... allows you to specify any color in the standard Windows color palette

 4. When you have finished fitting, go back to the File tab and click the "Output Costume Model" button.
    - The model will be output with the material, bones, rigid body, etc. adjusted accordingly.
    - If there is a risk of overwriting files, textures, etc. of the original model with the result of the changeover, the output will be aborted.
    - Some bones, such as the grip diffusion bone, are excluded from the output due to the difficulty of calculating hierarchy.

 Extra
   The model data in the folder "Mesh Compensating Elements" is an element model that I created in VRoid Studio.
   If the person model lacks mesh for areas such as the neck or above the elbows, this model can be loaded as a costume model,
   The fitting results can then be output to use a person model with the necessary mesh filled in.
   There are no restrictions, so please use it if you think it will work.
   If the mesh of the arms or other parts of the costume are weighted with weights other than the semi-standard bones, they are not eligible for support.


----------------------------------------------------------------
In case of problems
----------------------------------------------------------------

　The unzipped file is garbled.
　McAfee detects the presence of a virus.
　If you encounter any of these problems, please refer to the following page to see if the problem can be resolved. (This is the FAQ page for VMD Sizing)

　https://github.com/miu200521358/vmd_sizing/wiki/03.-%E5%95%8F%E9%A1%8C%E3%81%8C%E8%B5%B7%E3%81%8D%E3%81%9F%E5%A0%B4%E5%90%88

　If you still cannot solve the problem, please report it in the community.


----------------------------------------------------------------
Community
----------------------------------------------------------------

　Nikoni community: https://com.nicovideo.jp/community/co5387214

　　VMD sizing, motion supporter, and other homebrew tools.
　　You can try out the beta version of the site as soon as possible.
　　I would like to be able to follow up if the tool does not work properly.
　　The site is closed, but it is auto-approved, so please feel free to join!

----------------------------------------------------------------
Terms of use, etc.
----------------------------------------------------------------

　Required Information.

　　- If you publish or distribute a model with a change of clothes, please give credit where credit is due.
　　- In the case of Nico Nico Douga, please register the still image (im11209493) for the tree in the contents tree.
　　　 - If you register as a parent in the content tree, credit is optional.
　　- If you distribute your models to the general public, please clearly state the credit only in the distribution notice (video, etc.) and register the model in the content tree.
　　　 - It is not necessary to request a credit statement for works that use the model in question.

　Optional

　　- The following actions are permitted within the scope of the original model's terms and conditions.

　　- Adjustment and modification of changed models
　　　 - In the case of distributed models, please make sure that the terms of use allow for alterations.
　　- Posting videos of models on video-sharing sites, SNS, etc.
　　　 - Posting of models with costume settings created in progress is also acceptable.
　　　 - However, if the original model's terms and conditions stipulate a posting destination, age restrictions, etc., models dressed with this tool will also be subject to those terms and conditions.
　　- Distribution of models to an unspecified number of people
　　　 - Only self-made models or models for which distribution to an unspecified number of people is permitted.

　Prohibited items

　　- Please refrain from the following acts regarding this tool and generated models

　　- Actions that are outside the scope of the rules of the original model.
　　- Complete self-made statement.
　　- Actions that may cause inconvenience to the rights holders.
　　- Actions that are intended to defame or slander others (regardless of whether they are two-dimensional or three-dimensional).

　　- The following conditions are not prohibited, but we ask that you take them into consideration
　　　 - Use of images that contain excessive violence, obscenity, romantic, bizarre, political or religious expressions (R-15 or above).

　　　 - Please make sure to check the terms and conditions of the original model before using the work.
　　　 - Please be sure to check the scope of the terms and conditions of the original model, etc., before using the work.

　　- Please note that "commercial use" is not prohibited in this tool, but is prohibited in PMXEditor.

　Disclaimer

　　- Please use at your own risk.
　　- The author assumes no responsibility for any problems caused by the use of this tool.


----------------------------------------------------------------
Source code library
----------------------------------------------------------------

This tool is written in python, and the following libraries are used and included.

numpy (https://pypi.org/project/numpy/)
bezier (https://pypi.org/project/bezier/)
numpy-quaternion (https://pypi.org/project/numpy-quaternion/)
wxPython (https://pypi.org/project/wxPython/)
pyinstaller (https://pypi.org/project/PyInstaller/)

Source code is available on Github. (MIT License)
However, copyright is not waived.

https://github.com/miu200521358/pmx_dressup

Icons are borrowed from icon-rainbow
https://icon-rainbow.com/%E3%83%AF%E3%83%B3%E3%83%94%E3%83%BC%E3%82%B9%E3%81%AE%E7%84%A1%E6%96%99%E3%82%A2%E3%82%A4%E3%82%B3%E3%83 %B3%E7%B4%A0%E6%9D%90-2/


----------------------------------------------------------------
Credits
----------------------------------------------------------------

　Tool name: PmxDressup
　Author: miu or miu200521358

　http://www.nicovideo.jp/user/2776342
　Twitter: @miu200521358
　Mail: garnet200521358@gmail.com


----------------------------------------------------------------
History
----------------------------------------------------------------

PmxDressup_1.00.02 (2023/10/22)
Bug Fixes
 - Fixed a case where IK link bones were output and IK bones were not output.
 - The path consistency judgment when outputting a change of clothes model was checking for the existence of folders that had not yet been created, so this was removed.
 - Fixed an error when judging the movement offset of arm bones when there is no shoulder C.
 - Removed rotation fitting for neck and head.
 - Added processing to ignore X for trunk movement and YZ for rotation.
 - Fixed output of parent bones when child bones are output targets.
 - Fixed output of rigid bodies to which no bones are attached

PmxDressup_1.00.01 (2023/08/10)
Function additions and modifications
 - Adjustment to allow changing of cat ears and other parts
 - Added SDEF parameter recalculation process
 - Adjusted semi-non-standard fittings such as sleeve IK
 - Modified shoe size to be determined by the ratio of shoe soles (width in Z direction) of the person and costume
 - Added upper body 3 as a semi-standard check target
 - Added skip processing so that grip diffusion system is not output
Bug fixes
 - Fixed a case where costume morphs did not fit in the display frame
 - Fixed a case where costume morphs did not fit into the display frame.
 - Fixed Y-rotation not being the same for left and right when adjusting ankles and other parts of the body globally.
 - Excluded head and neck from reference bones when adjusting bone positions for upper and lower body
 - Fixed wrong output judgment of IK bone when outputting a change of clothes model.
 - Fixed to remove characters in PMX model name that cannot be output to file.

PmxDressup_1.00.00 (2023/08/20)
 General distribution starts

