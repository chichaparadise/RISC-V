#!/bin/bash

exe_file=./test.py;

asm_tests=(
          simple
          add addi
          and andi
          auipc
          beq bge bgeu blt bltu bne
          j jal jalr
        #   lw
          lui
          or ori
          sw
          sll slli
          slt slti
          sra srai
          srl srli
          sub
          xor xori
      );
vmh_dir=./programs/build/assembly/bin;

SOFTWARE_SOCKET_NAME=/tmp/connectal$USER
export SOFTWARE_SOCKET_NAME

log_dir=logs
wait_time=3

# create bsim log dir
mkdir -p ${log_dir}

# run each test
for test_name in ${asm_tests[@]}; do
	echo "-- benchmark test: ${test_name} --"
	# copy vmh file
	export mem_file=${vmh_dir}/${test_name}.riscv
	if [ ! -f $mem_file ]; then
		echo "ERROR: $mem_file does not exit, you need to first compile"
		exit
	fi

	# run test
    python3 ${exe_file}

done
