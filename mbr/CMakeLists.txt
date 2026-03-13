# OSDMenu MBR

# Base sources
set(EE_SOURCES
    src/main.c
    src/init.c
    src/handlers.c
    src/config.c
    src/crypto.c
    src/hdd.c
    src/common.c
    src/disc.c
)

# Common files
list(APPEND EE_SOURCES
    ../common/src/cnf.c
    ../common/src/history.c
    ../common/src/game_id.c
    ../common/src/loader.c
    ../common/src/patinfo.c
)

# IRX files
set(IRX_FILES
    iomanX.irx
    fileXio.irx
    ps2dev9.irx
    bdm.irx
    bdmfs_fatfs.irx
    ata_bd.irx
    ps2hdd-osd.irx
    ps2fs.irx
    secrsif.irx
)

# Resource files
set(RES_FILES
    icon_A.sys
    icon_C.sys
    icon_J.sys
)

set(EE_LIBS
    patches
    dma
    libdebug.a
    fileXio
    secr
    pad
    gskit
    dmakit
    mc
)

# If set, define UDPTTY IP and add smap_udptty
if(ENABLE_PRINTF)
    add_compile_definitions(ENABLE_PRINTF UDPTTYIP="${UDPTTY_IP}")
    # smap_udptty target is built by the launcher
    list(APPEND IRX_FILES smap_udptty.irx)
endif()

# Process IRX files
set(IRX_SOURCES)
foreach(irx ${IRX_FILES})
    get_filename_component(irx_name ${irx} NAME_WE)
    string(REPLACE "-" "_" irx_name_clean ${irx_name})

    if(irx_name STREQUAL "smap_udptty")
        # smap_udptty is not a part of PS2SDK
        irx_to_source("${CMAKE_SOURCE_DIR}/launcher/iop/smap_udptty/smap_udptty.irx" irx_source "smap_udptty_irx" "")
    else()
        irx_to_source("$ENV{PS2SDK}/iop/irx/${irx}" irx_source "${irx_name_clean}_irx" "")
    endif()

    list(APPEND IRX_SOURCES ${irx_source})
endforeach()

# Embed the loader and PS1VN
set(ELF_SOURCES)
elf_to_source(loader loader_source "loader_elf" "")
list(APPEND ELF_SOURCES ${loader_source})
elf_to_source(ps1vn ps1vn_source "ps1vn_elf" "")
list(APPEND ELF_SOURCES ${ps1vn_source})

# Process resource files
set(RES_SOURCES)
foreach(res ${RES_FILES})
    get_filename_component(res_name ${res} NAME_WE)
    bin2c_source("${CMAKE_SOURCE_DIR}/common/res/${res}" res_source "${res_name}_sys")
    list(APPEND RES_SOURCES ${res_source})
endforeach()

# Create executable
add_executable(osdmbr ${EE_SOURCES} ${IRX_SOURCES} ${ELF_SOURCES} ${RES_SOURCES})

# Build smap_udptty dependency
if(ENABLE_PRINTF)
    add_dependencies(osdmbr smap_udptty)
endif()

target_include_directories(osdmbr PRIVATE
    ../common/include
    include
)

target_compile_options(osdmbr PRIVATE
    -O2
    -G0
    -Wall
    -Werror
    -fdata-sections
    -ffunction-sections
)

# Use custom linker script
target_link_options(osdmbr PRIVATE
    -T${CMAKE_CURRENT_SOURCE_DIR}/linkfile
)

link_newlib_nano(osdmbr
    patches
    dma
    libdebug.a
    fileXio
    secr
    pad
    gskit
    dmakit
    mc
    kernel
    cdvd
    cglue
    pthread
    pthreadglue
)

if(DEBUG)
    set(mbr_link_flags "-Wl,--gc-sections")
else()
    set(mbr_link_flags "-Wl,--gc-sections -s")
endif()
set_target_properties(osdmbr PROPERTIES
    LINK_FLAGS "${mbr_link_flags}"
    OUTPUT_NAME "osdmbr"
    RUNTIME_OUTPUT_NAME "osdmbr.elf"
)

# Create binary version
add_custom_command(
    TARGET osdmbr POST_BUILD
    COMMAND ${CMAKE_OBJCOPY} -O binary -v "$<TARGET_FILE:osdmbr>" "${CMAKE_CURRENT_BINARY_DIR}/osdmbr.bin"
    COMMENT "Creating binary from ELF"
)

# Build KELF if MG key environment variables are set or PS2KEYS.dat exists
if(DEFINED ENV{MG_SIG_MASTER_KEY} OR EXISTS "${CMAKE_SOURCE_DIR}/utils/scripts/PS2KEYS.dat")
    add_custom_command(
        TARGET osdmbr POST_BUILD
        COMMAND ${CMAKE_COMMAND} -E env
            MG_SIG_MASTER_KEY=$ENV{MG_SIG_MASTER_KEY}
            MG_SIG_HASH_KEY=$ENV{MG_SIG_HASH_KEY}
            MG_KBIT_MASTER_KEY=$ENV{MG_KBIT_MASTER_KEY}
            MG_KBIT_IV=$ENV{MG_KBIT_IV}
            MG_KC_MASTER_KEY=$ENV{MG_KC_MASTER_KEY}
            MG_KC_IV=$ENV{MG_KC_IV}
            MG_ROOTSIG_MASTER_KEY=$ENV{MG_ROOTSIG_MASTER_KEY}
            MG_ROOTSIG_HASH_KEY=$ENV{MG_ROOTSIG_HASH_KEY}
            MG_CONTENT_TABLE_IV=$ENV{MG_CONTENT_TABLE_IV}
            MG_CONTENT_IV=$ENV{MG_CONTENT_IV}
            ${PYTHON3} "${CMAKE_SOURCE_DIR}/utils/scripts/kelfsign.py" mbr "${CMAKE_CURRENT_BINARY_DIR}/osdmbr.bin" "${CMAKE_CURRENT_BINARY_DIR}/OSDMBR.XLF"
        COMMENT "Creating KELF file"
    )
    message(STATUS "MBR KELF build enabled")
endif()
